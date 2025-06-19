# consumers.py

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import json, os, base64, asyncio, logging
from urllib.parse import parse_qs
from cryptography.fernet import Fernet
from collections import defaultdict
from django.conf import settings
from django.db.models import Q
from .models import Employee
from chat.models import EmployeeChat
from .serializers import EmployeeSerializers

logger = logging.getLogger(__name__)


class EmployeeList(AsyncWebsocketConsumer):
    async def connect(self):
        query_params = parse_qs(self.scope["query_string"].decode())
        self.employee_mail = query_params.get("employee_mail", [None])[0]

        if not self.employee_mail:
            await self.close()
            return

        await self.accept()
        self.notification_task = None

        try:
            self.keys = self.load_key()
            self.employee = await self.get_employee(self.employee_mail)
            self.emp_id = self.employee.employee_id
            self.org_id, self.orgn_name = await self.get_org_details(self.employee)
            self.employee_data = EmployeeSerializers(self.employee).data
            self.other_employees = await self.get_other_employees(self.org_id, self.employee.id)

            await self.send_initial_data()

            # Start background notification task
            self.notification_task = asyncio.create_task(self.send_periodic_notifications())
        except Exception as e:
            logger.exception("Error during connection setup")
            await self.send_error("Internal server error during connection.")
            await self.close()

    async def disconnect(self, close_code):
        if self.notification_task:
            self.notification_task.cancel()
            try:
                await self.notification_task
            except asyncio.CancelledError:
                pass

    async def send_initial_data(self):
        notifications = await database_sync_to_async(self.get_unread_notifications_count)(self.emp_id)
        employees_list = await database_sync_to_async(self.prepare_employee_list)(
            self.emp_id, self.other_employees, self.orgn_name, notifications
        )

        await self.send(json.dumps({
            "Status": "Success",
            "Data": self.employee_data,
            "message": "Login Successful",
            "Org_Employees": {
                "count_type": "unread_count",
                "chat_receiver": self.emp_id,
                "count": notifications["unread_count"],
                "unread_sender_count": notifications["unread_sender"],
                "unread_messages": notifications["unread_messages"],
                "employee_list": employees_list
            }
        }))

    async def receive(self, text_data):
        # No dynamic receive for now
        pass

    async def send_periodic_notifications(self):
        try:
            while True:
                await asyncio.shield(self.send_notifications_update())
                await asyncio.sleep(3)  # Optimal balance for real-time and performance
        except asyncio.CancelledError:
            logger.info("Notification task cancelled")

    async def send_notifications_update(self):
        notifications = await database_sync_to_async(self.get_unread_notifications_count)(self.emp_id)
        employees_list = await database_sync_to_async(self.prepare_employee_list)(
            self.emp_id, self.other_employees, self.orgn_name, notifications
        )

        await self.send(json.dumps({
            "Data": self.employee_data,
            "Org_Employees": {
                "count_type": "unread_count",
                "chat_receiver": self.emp_id,
                "count": notifications["unread_count"],
                "unread_sender_count": notifications["unread_sender"],
                "unread_messages": notifications["unread_messages"],
                "employee_list": employees_list
            }
        }, ensure_ascii=False))

    async def send_error(self, message):
        await self.send(json.dumps({"Status": "Error", "message": message}))

    @database_sync_to_async
    def get_employee(self, email):
        return Employee.objects.select_related("user", "organisation").get(user__email=email)

    @database_sync_to_async
    def get_org_details(self, employee):
        org = employee.organisation
        return org.id, org.name or org.email

    @database_sync_to_async
    def get_other_employees(self, org_id, exclude_id):
        return list(Employee.objects.select_related("user").filter(organisation_id=org_id).exclude(id=exclude_id))

    def load_key(self):
        path = os.path.join(settings.BASE_DIR, 'Encryption_Key.key')
        if os.path.exists(path):
            with open(path, 'r') as f:
                return [base64.urlsafe_b64decode(k.strip()) for k in f.readlines()]
        return []

    def decrypt_message(self, content):
        for key in self.keys:
            try:
                return Fernet(key).decrypt(content.encode()).decode()
            except Exception:
                continue
        return None

    def get_unread_notifications_count(self, emp_id):
        unread_messages = []
        unread_by_sender = defaultdict(lambda: {"unread_count_sender": 0, "messages": []})

        for chat in EmployeeChat.objects.filter(Q(receiver__employee_id=emp_id)):
            for msg in chat.messages:
                if msg.get("receiver") == emp_id and not msg.get("read", False):
                    sender = msg.get("sender")
                    content = msg.get("content")
                    decrypted = self.decrypt_message(content)
                    if decrypted:
                        msg["unread_message"] = decrypted
                    unread_by_sender[sender]["unread_count_sender"] += 1
                    unread_by_sender[sender]["messages"].append(msg)
                    unread_messages.append(msg)

        return {
            "receiver": emp_id,
            "unread_count": len(unread_messages),
            "unread_sender": len(unread_by_sender),
            "unread_messages": [
                {"sender": s, "receiver": emp_id, **d}
                for s, d in unread_by_sender.items()
            ]
        }

    def prepare_employee_list(self, current_emp_id, employees, org_name, notifications):
        unread_by_sender = {
            n['sender']: n for n in notifications['unread_messages']
        }
        result = []

        for emp in employees:
            try:
                chat = EmployeeChat.objects.filter(
                    Q(sender__employee_id=emp.employee_id, receiver__employee_id=current_emp_id) |
                    Q(sender__employee_id=current_emp_id, receiver__employee_id=emp.employee_id)
                ).order_by('-timestamp').first()

                latest_msg_data = {"content": None}
                if chat and chat.messages:
                    latest_msg = sorted(chat.messages, key=lambda m: m.get("timestamp", ""), reverse=True)[0]
                    decrypted = self.decrypt_message(latest_msg.get("content"))
                    latest_msg_data = latest_msg | {"content": decrypted}

                unread_info = unread_by_sender.get(emp.employee_id, {"unread_count_sender": 0, "messages": []})

                result.append({
                    "employee_id": emp.employee_id,
                    "employee_data": {
                        "name": emp.user.name,
                        "image": emp.image.url if emp.image else None,
                        "email": emp.user.email,
                        "status": emp.status,
                        "company": org_name,
                    },
                    "id": emp.id,
                    "latest_message": latest_msg_data,
                    "unread_notifications": {
                        "sender": emp.employee_id,
                        "receiver_employee_id": current_emp_id,
                        "total_unread_count": unread_info["unread_count_sender"],
                        "unread_messages": unread_info["messages"]
                    }
                })

            except Exception as e:
                logger.exception("Error in prepare_employee_list")

        result.sort(key=lambda x: (x.get("latest_message") or {}).get("timestamp", ""), reverse=True)
        return result
