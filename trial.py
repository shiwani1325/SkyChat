import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from datetime import datetime
import json
import asyncio
import os
import uuid
import base64
from cryptography.fernet import Fernet
from django.conf import settings
from django.db.models import Q
# from .views import EncryptionMixin


class NotificationTest(AsyncWebsocketConsumer):
    async def connect(self):
        self.employee_id = self.scope['url_route']['kwargs']['employee_id']
        self.notification_group_name = f'notification_{self.employee_id}'

        await self.channel_layer.group_add(
            self.notification_group_name,
            self.channel_name
        )
        await self.accept()
        self.periodic_task = asyncio.create_task(self.send_periodic_notifications())

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.notification_group_name,
            self.channel_name
        )
        self.periodic_task.cancel()

    async def receive(self, text_data):
        data = json.loads(text_data)
        command = data.get('command')

        if command == 'mark_read':
            sender_id = data.get('sender_id')
            success = await self.mark_messages_read(sender_id)
            if success:
                await self.send_notifications_update()
        else:
            await self.send_notifications_update()

    async def send_notification(self, event):
        await self.send(text_data=json.dumps({
            'type': 'new_notification',
            'notification': event['data']
        }))
        await self.send_notifications_update()

    async def send_notifications_update(self):
        unread_count = await sync_to_async(self.get_unread_notifications_count)(self.employee_id)
        sorted_employee_list_view = await self.get_employee_list(self.employee_id)
        

        await self.send(text_data=json.dumps({
            'count_type': 'unread_count',
            'chat_receiver': unread_count['receiver'],
            'count': unread_count['unread_count'],
            "unread_sender_count": unread_count['unread_sender'],
            'unread_messages': unread_count['unread_messages'],
            'employee_list': sorted_employee_list_view
        }, ensure_ascii=False))

    async def send_periodic_notifications(self):
        while True:
            await self.send_notifications_update()
            await asyncio.sleep(1)


    
    
    def load_key(self):
        key_file_path = os.path.join(settings.BASE_DIR, 'Encryption_Key.key')
        if os.path.exists(key_file_path):
            with open(key_file_path, 'r') as key_file:
                key_base64_list = key_file.readlines()
            keys = [base64.urlsafe_b64decode(key.strip()) for key in key_base64_list]
            return keys
        else:
            print(f"Encryption key file not found at {key_file_path}")
        return []

    def decrypt_message(self, encrypted_content, encryption_key):
        try:
            fernet = Fernet(encryption_key)
            decrypted_content = fernet.decrypt(encrypted_content.encode()).decode()
            return decrypted_content
        except Exception as e:
            # return f"Error decrypting message: {str(e)}"
            return None





    def get_unread_notifications_count(self, employee_id):
        from collections import defaultdict
        from .models import EmployeeChat
        keys = self.load_key()

        unread_messages = []
        unread_messages_by_sender = defaultdict(lambda: {"unread_count_sender": 0, "messages": []})

        unread_count = 0
        chats = EmployeeChat.objects.filter(
            Q(receiver__employee_id=employee_id) | Q(messages__icontains=employee_id))

        for chat in chats:
            for msg in chat.messages:
                if msg.get('receiver') == employee_id and not msg.get('read', False):
                    unread_count += 1
                    sender_id = msg.get('sender')

                    if msg.get('deleted', False):
                        decrypted_content = "Deleted message"
                    
                    else:   
                        encrypted_content = msg.get('content', "")
                        decrypted_content = encrypted_content

                        if encrypted_content and keys:  
                            for encryption_key in keys:
                                try:
                                    decrypted_content = self.decrypt_message(encrypted_content, encryption_key)
                                    # if "Error decrypting message" not in decrypted_content:
                                    if decrypted_content is not None:
                                        break
                                except Exception as e:
                                    print(f"Decryption failed with key {encryption_key}: {str(e)}")

                    msg["unread_message"] = decrypted_content         
                    unread_messages_by_sender[sender_id]["unread_count_sender"] += 1
                    unread_messages_by_sender[sender_id]["messages"].append(msg)
                    unread_messages.append(msg)

        unread_count = len(unread_messages)
        formatted_unread_messages = [
            {"sender": sender, "receiver": employee_id, **data} for sender, data in unread_messages_by_sender.items()
        ]

        return {
            "receiver": employee_id,
            "unread_count": unread_count,
            "unread_sender": len(unread_messages_by_sender),
            "unread_messages": formatted_unread_messages
        }

    @database_sync_to_async
    def mark_messages_read(self, sender_id):
        from .models import EmployeeChat
        try:
            chats = EmployeeChat.objects.filter(
                Q(receiver__employee_id=self.employee_id) | Q(messages__icontains=self.employee_id)
            )
            updated = False
            for chat in chats:
                modified_messages = []
                for msg in chat.messages:
                    if msg.get('sender') == sender_id and msg.get('receiver') == self.employee_id:
                        if not msg.get('read', False):
                            msg['read'] = True
                            msg['read_at'] = datetime.now().isoformat()
                            updated = True
                    modified_messages.append(msg)
                if updated:
                    chat.messages = modified_messages
                    chat.save()
            return updated
        except Exception as e:
            print(f"Exception error in mark messages read:{e}")
            return False

    async def get_employee_list(self, receiver_id):
        from .models import Employee, EmployeeChat
        from .serializers import EmployeeSerializer, EmployeeChatSerializer

        try:
            keys = self.load_key()
            employee_list = await sync_to_async(list)(Employee.objects.all().order_by('-id'))
            # print(f"employee list is here :{employee_list}")
            serializer = EmployeeSerializer(employee_list, many=True)

            latest_employee_chats = []

            for employee in employee_list:
                receiver = await sync_to_async(lambda: Employee.objects.get(employee_id=receiver_id))()
                print(f"receiver is :{receiver}")

                try:
                    latest_message = await sync_to_async(lambda: EmployeeChat.objects.filter(
                        Q(sender=employee, receiver=receiver) | Q(sender=receiver, receiver=employee)
                    ).order_by('-timestamp').first())()

                    if latest_message:
                        if latest_message.messages and len(latest_message.messages) > 0:
                            latest_msg = sorted(
                                latest_message.messages,
                                key=lambda x: x.get('timestamp', ''),
                                reverse=True
                            )[0]

                            encrypted_content = latest_msg.get("content")
                            latest_msg_sender = latest_msg.get("sender", "")
                            latest_msg_receiver = latest_msg.get("receiver", "")
                            # print(f"latest message sender name :{latest_msg.get('sender_name')}")

                            if encrypted_content and keys:
                                # decrypted_content = "No matching encryption key found"
                                decrypted_content = None
                                for encryption_key in keys:
                                    try:
                                        decrypted_content = self.decrypt_message(encrypted_content, encryption_key)
                                        # if "Error decrypting message" not in decrypted_content:
                                        if decrypted_content is not None:
                                            break 
                                    except Exception as e:
                                        print(f"Decryption failed with key {encryption_key}: {str(e)}")
                            else:
                                decrypted_content = None

                            notifications = await sync_to_async(self.get_unread_notifications_count)(receiver_id)
                              
                            unread_messages_for_employee = [
                                {
                                    "sender": msg["sender"],
                                    "receiver": msg["receiver"],
                                    "unread_count": msg.get("unread_count_sender", 0),
                                    "messages": msg["messages"]
                                }
                                for msg in notifications["unread_messages"]
                                if msg["sender"] == employee.employee_id
                            ]
                            

                            latest_employee_chats.append({
                                "employee_id": employee.employee_id,
                                "id": latest_message.id,
                                "employee_data": {
                                    "name": employee.name,
                                    "image": employee.image,
                                    "email": employee.email,
                                    "status": employee.status,
                                    "company": employee.company
                                },
                                "latest_message": {
                                    "sender": latest_msg.get("sender", ""),
                                    "receiver": latest_msg.get("receiver", ""),
                                    "sender_name":latest_msg.get("sender_name",""),
                                    "receiver_name":latest_msg.get("receiver_name",""),
                                    "content": decrypted_content,
                                    "file": latest_msg.get("file", latest_message.file.url if latest_message.file else None),
                                    "timestamp": latest_msg.get("timestamp", ""),
                                    "read": latest_msg.get("read", False),
                                    "unread": not latest_msg.get("read", False)
                                },
                                "unread_notifications": {
                                    "sender": unread_messages_for_employee[0]['sender'] if unread_messages_for_employee else [],
                                    "receiver_employee_id": unread_messages_for_employee[0]['receiver'] if unread_messages_for_employee else [],
                                    "total_unread_count": unread_messages_for_employee[0]['unread_count'] if unread_messages_for_employee else 0,
                                    "unread_messages": unread_messages_for_employee
                                }
                            })
                        else:
                            latest_employee_chats.append({
                                "employee_id": employee.employee_id,
                                "employee_data": {
                                    "name": employee.name,
                                    "image": employee.image,
                                    "email": employee.email,
                                    "status": employee.status,
                                    "company": employee.company
                                },
                                "id": None,
                                "latest_message": None,
                                "unread_notifications": {"unread_count": 0, "unread_sender": 0, "unread_messages": []}
                            })
                    else:
                        latest_employee_chats.append({
                            "employee_id": employee.employee_id,
                            "employee_data": {
                                "name": employee.name,
                                "image": employee.image,
                                "email": employee.email,
                                "status": employee.status,
                                "company": employee.company
                            },
                            "id": None,
                            "latest_message": None,
                            "unread_notifications": {"unread_count": 0, "unread_sender": 0, "unread_messages": []}
                        })
                
                except Exception as emp_error:
                    print(f"Error processing employee {employee.employee_id}: {str(emp_error)}")
                    continue

            latest_employee_chats.sort(
                key=lambda x: (x.get("latest_message", {}) or {}).get("timestamp", ""),
                reverse=True
            )

            # # Saving the employee list to a JSON file
            # employee_list_file = os.path.join(settings.BASE_DIR, 'employee_list.json')
            # with open(employee_list_file, 'w') as f:
            #     json.dump(latest_employee_chats, f, ensure_ascii=False, indent=4)

        except Exception as e:
            print(f"Global error in EmployeeList.get: {str(e)}")

        return latest_employee_chats