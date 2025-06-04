from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
import json
from .models import Employee
from chat.models import EmployeeChat
from .serializers import EmployeeSerializers
import asyncio
import os
import base64
from cryptography.fernet import Fernet
from django.conf import settings
from django.db.models import Q
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class EmployeeList(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'periodic_task'):
            self.periodic_task.cancel()

    async def receive(self, text_data):
        request_data = json.loads(text_data)
        employee_mail = request_data.get('employee_mail')

        try:
            employee = await self.get_employee(employee_mail)
            self.emp_id = employee.employee_id
            org_id, org_name = await self.get_org_details(employee)
            self.orgn_name = org_name
            serializer = EmployeeSerializers(employee)
            self.employee_data = serializer.data
            # print(f"employee data :{self.employee_data}")
            other_employees = await self.get_other_employee(org_id, employee.id)
            self.other_employee = other_employees
            notifications = await sync_to_async(self.get_unread_notifications_count)(employee.employee_id)
            self.notify = notifications
            self.periodic_task = asyncio.create_task(self.send_periodic_notifications())
            employees_list = await database_sync_to_async(self.prepare_employee_list)(
                current_employee_id=employee.employee_id,
                employees=other_employees,
                org_name=org_name,
                notifications=notifications
            )

            await self.send(text_data=json.dumps({
                "Status": "Success",
                "Data": self.employee_data,
                "message": "Login Successful",
                "Org_Employees": {
                    "count_type": "unread_count",
                    "chat_receiver": employee.employee_id,
                    "count": notifications["unread_count"],
                    "unread_sender_count": notifications["unread_sender"],
                    "unread_messages": notifications["unread_messages"],
                    "employee_list": employees_list
                }
            }))

        except Employee.DoesNotExist:
            await self.send(text_data=json.dumps({
                "Status": "Error",
                "message": "Employee not found"
            }))
        except Exception as e:
            logger.exception("Error in receive method: %s", e)
            await self.send(text_data=json.dumps({
                "Status": "Error",
                "message": "An internal error occurred."
            }))

    async def send_periodic_notifications(self):
        try:
            while True:
                await self.send_notifications_update()
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass

    async def send_notifications_update(self):
        unread_count = await sync_to_async(self.get_unread_notifications_count)(self.emp_id)
        sorted_employee_list_view = await database_sync_to_async(self.prepare_employee_list)(
            self.emp_id, self.other_employee, self.orgn_name, unread_count)

        await self.send(text_data=json.dumps({
            "Data": self.employee_data,
            "Org_Employees": {
                'count_type': 'unread_count',
                'chat_receiver': unread_count['receiver'],
                'count': unread_count['unread_count'],
                "unread_sender_count": unread_count['unread_sender'],
                'unread_messages': unread_count['unread_messages'],
                'employee_list': sorted_employee_list_view
            }
        }, ensure_ascii=False))

    @database_sync_to_async
    def get_employee(self, employee_mail):
        return Employee.objects.select_related("user").get(user__email=employee_mail)

    @database_sync_to_async
    def get_other_employee(self, org_id, excluded_emp_id):
        return list(Employee.objects.select_related("user").filter(organisation_id=org_id).exclude(id=excluded_emp_id))


    @sync_to_async
    def get_org_details(self, employee):
        org = employee.organisation
        return org.id, org.name or org.email

    def prepare_employee_list(self, current_employee_id, employees, org_name, notifications):
        keys = self.load_key()
        unread_by_sender = {
            n['sender']: n for n in notifications['unread_messages']
        }
        employee_list = []

        for emp in employees:
            latest_msg = None
            try:
                chat = EmployeeChat.objects.filter(
                    Q(sender__employee_id=emp.employee_id, receiver__employee_id=current_employee_id) |
                    Q(sender__employee_id=current_employee_id, receiver__employee_id=emp.employee_id)
                ).order_by('-timestamp').first()

                if chat and chat.messages:
                    sorted_msgs = sorted(chat.messages, key=lambda m: m.get('timestamp', ''), reverse=True)
                    encrypted_content = sorted_msgs[0].get("content")
                    decrypted = encrypted_content
                    for k in keys:
                        try:
                            dec = self.decrypt_message(encrypted_content, k)
                            if dec:
                                decrypted = dec
                                break
                        except:
                            continue
                    latest_msg = decrypted

                    unread_info = unread_by_sender.get(emp.employee_id, {"unread_count_sender": 0, "messages": []})

                    employee_list.append({
                        "employee_id": emp.employee_id,
                        "employee_data": {
                            "name": emp.user.name,
                            "image": emp.image.url if emp.image else None,
                            "email": emp.user.email,
                            "status": emp.status,
                            "company": org_name,
                        },
                        "id": emp.id,
                        "latest_message": sorted_msgs[0] | {"content": latest_msg},
                        "unread_notifications": {
                            "sender": emp.employee_id,
                            "receiver_employee_id": current_employee_id,
                            "total_unread_count": unread_info["unread_count_sender"],
                            "unread_messages": unread_info["messages"]
                        }
                    })
                else:
                    employee_list.append({
                        "employee_id": emp.employee_id,
                        "employee_data": {
                            "name": emp.user.name,
                            "image": emp.image.url if emp.image else None,
                            "email": emp.user.email,
                            "status": emp.status,
                            "company": org_name,
                        },
                        "id": emp.id,
                        "latest_message": {"content": latest_msg},
                        "unread_notifications": {"unread_count": 0, "unread_sender": 0, "unread_messages": []}
                    })
            except Exception as e:
                logger.exception("Error preparing employee list for %s: %s", emp.user.email, e)

        employee_list.sort(
            key=lambda x: (x.get("latest_message", {}) or {}).get("timestamp", ""),
            reverse=True
        )
        return employee_list

    def load_key(self):
        key_file_path = os.path.join(settings.BASE_DIR, 'Encryption_Key.key')
        if os.path.exists(key_file_path):
            with open(key_file_path, 'r') as key_file:
                key_base64_list = key_file.readlines()
            return [base64.urlsafe_b64decode(key.strip()) for key in key_base64_list]
        return []

    def decrypt_message(self, encrypted_content, encryption_key):
        try:
            fernet = Fernet(encryption_key)
            return fernet.decrypt(encrypted_content.encode()).decode()
        except:
            return None

    def get_unread_notifications_count(self, employee_id):
        unread_messages = []
        unread_by_sender = defaultdict(lambda: {"unread_count_sender": 0, "messages": []})
        keys = self.load_key()

        for chat in EmployeeChat.objects.filter(Q(receiver__employee_id=employee_id)):
            for msg in chat.messages:
                if msg.get("receiver") == employee_id and not msg.get("read", False):
                    sender = msg.get("sender")
                    decrypted = msg.get("content")
                    for k in keys:
                        try:
                            dec = self.decrypt_message(decrypted, k)
                            if dec:
                                decrypted = dec
                                break
                        except:
                            continue
                    msg["unread_message"] = decrypted
                    unread_by_sender[sender]["unread_count_sender"] += 1
                    unread_by_sender[sender]["messages"].append(msg)
                    unread_messages.append(msg)

        return {
            "receiver": employee_id,
            "unread_count": len(unread_messages),
            "unread_sender": len(unread_by_sender),
            "unread_messages": [
                {"sender": s, "receiver": employee_id, **d} for s, d in unread_by_sender.items()
            ]
        }
