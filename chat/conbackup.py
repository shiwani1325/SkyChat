# employee/consumers.py

import json
import os
import re
import uuid
import base64
import asyncio
from datetime import datetime
from cryptography.fernet import Fernet
from django.conf import settings
from django.db.models import Q
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from employee.models import Employee
from .utils import generate_and_save_key, load_keys

class EmployeeChat(AsyncWebsocketConsumer):
    ACTIVE_USERS = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.key = None
        self.sender_id = None
        self.receiver_id = None
        self.emp_room_group_name = None

    async def connect(self):
        self.sender_id = self.scope['url_route']['kwargs']['sender_id']
        self.receiver_id = self.scope['url_route']['kwargs']['receiver_id']
        self.emp_room_group_name = f'emp_room_{min(self.sender_id, self.receiver_id)}_{max(self.sender_id, self.receiver_id)}'
        self.__class__.ACTIVE_USERS[self.sender_id] = self.emp_room_group_name

        await self.channel_layer.group_add(self.emp_room_group_name, self.channel_name)
        await self.accept()

        if (self.sender_id in self.__class__.ACTIVE_USERS and
            self.receiver_id in self.__class__.ACTIVE_USERS and
            self.__class__.ACTIVE_USERS[self.receiver_id] == self.emp_room_group_name):
            await self.mark_all_messages_read(self.receiver_id, self.sender_id)

    async def disconnect(self, close_code):
        self.__class__.ACTIVE_USERS.pop(self.sender_id, None)
        await self.channel_layer.group_discard(self.emp_room_group_name, self.channel_name)

    async def mark_all_messages_read(self, receiver_id, sender_id):
        from .models import EmployeeChat as EmployeeChatModel
        try:
            chats = await database_sync_to_async(list)(EmployeeChatModel.objects.filter(
                Q(sender__employee_id=sender_id, receiver__employee_id=receiver_id) |
                Q(sender__employee_id=receiver_id, receiver__employee_id=sender_id)
            ))
            updated_messages = []

            for chat in chats:
                modified = False
                for msg in chat.messages:
                    if not msg.get("read", True):
                        msg["read"] = True
                        updated_messages.append(msg)
                        modified = True
                if modified:
                    chat.messages = chat.messages
                    await database_sync_to_async(chat.save)(update_fields=["messages"])

            if updated_messages:
                await self.channel_layer.group_send(
                    self.emp_room_group_name,
                    {'type': "updating_existing_message", "updated_messages": updated_messages}
                )
        except Exception as e:
            print(f"Error: {e}")

    async def updating_existing_message(self, event):
        for msg in event["updated_messages"]:
            await self.update_message_in_cache(msg)

    async def update_message_in_cache(self, updated_msg):
        keys = load_keys()
        if not keys: return

        self.key = keys[-1]
        cipher_suite = Fernet(self.key)
        if updated_msg['content']:
            updated_msg['content'] = cipher_suite.decrypt(updated_msg['content'].encode()).decode()

        await self.send(text_data=json.dumps({"type": "message_update", "updated_message": updated_msg}))

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        sender_id = data.get('sender')
        receiver_ids = data.get('receiver', [])
        message_type = data.get('type', 'message')
        message_content = data.get('content')
        media_files = data.get('file', [])
        replied_to = data.get('replied_to')
        forwarded_content = data.get('forwarded_content', [])

        generate_and_save_key()
        keys = load_keys()
        if not keys:
            return await self.send(text_data=json.dumps({"error": "Encryption key not found"}))

        self.key = keys[-1]
        cipher_suite = Fernet(self.key)
        encrypted_content = cipher_suite.encrypt(message_content.encode()).decode() if message_content else None

        files_info = [await self.save_uploaded_file(f, sender_id) for f in media_files]
        sender_obj = await database_sync_to_async(Employee.objects.get)(employee_id=sender_id)
        sender_name = await database_sync_to_async(lambda: sender_obj.user.name)()

        for receiver_id in receiver_ids:
            message_id = str(uuid.uuid4())
            read = self.__class__.ACTIVE_USERS.get(receiver_id) == self.emp_room_group_name
            receiver_obj = await database_sync_to_async(Employee.objects.get)(employee_id=receiver_id)
            receiver_name = await database_sync_to_async(lambda: receiver_obj.user.name)()

            message_data = await self.save_chat_message(
                sender_id, receiver_id,
                sender_name, receiver_name,
                encrypted_content, files_info, message_id, "sent", read,
                message_type, replied_to, forwarded_content
            )

            await self.channel_layer.group_send(
                self.emp_room_group_name,
                {
                    **message_data,
                    'type': 'chat_message',
                    'Activity': "Online" if read else "Offline"
                }
            )

    async def chat_message(self, event):
        keys = load_keys()
        if not keys:
            return await self.send(text_data=json.dumps({"error": "Key missing"}))

        self.key = keys[-1]
        cipher_suite = Fernet(self.key)
        decrypted_content = cipher_suite.decrypt(event['content'].encode()).decode() if event['content'] else None

        event['content'] = decrypted_content
        await self.send(text_data=json.dumps(event, ensure_ascii=False))

    @database_sync_to_async
    def save_chat_message(self, sender_id, receiver_id, sender_name, receiver_name,
                          content, files_info, message_id, status, read,
                          message_type='message', replied_to=None, forwarded_content=None):
        from .models import EmployeeChat as EmployeeChatModel
        from employee.models import Employee

        sender, receiver = sorted(
            [Employee.objects.get(employee_id=sender_id),
             Employee.objects.get(employee_id=receiver_id)],
            key=lambda emp: emp.employee_id
        )

        chat_obj, _ = EmployeeChatModel.objects.get_or_create(sender=sender, receiver=receiver)

        message = {
            'sender_id': sender_id,
            'receiver_id': receiver_id,
            'sender_name': sender_name,
            'receiver_name': receiver_name,
            'content': content,
            'file': files_info,
            'read': read,
            'message_id': message_id,
            'status': status,
            'message_type': message_type
        }

        if message_type == 'reply':
            message['replied_to'] = replied_to
        elif message_type == 'forward':
            message['forwarded_content'] = forwarded_content

        chat_obj.add_message(**message)
        return message

    async def save_uploaded_file(self, file_data, sender_id):
        try:
            format_info, b64_data = file_data.split(';base64,')
            ext = format_info.split('/')[-1]
            if ext not in ['jpg', 'jpeg', 'png', 'pdf', 'txt', 'docx', 'xls', 'xlsx']:
                return None

            filename = f"{sender_id}_{uuid.uuid4()}.{ext}"
            file_dir = os.path.join(settings.MEDIA_ROOT, 'files')
            os.makedirs(file_dir, exist_ok=True)

            file_path = os.path.join(file_dir, filename)
            with open(file_path, 'wb') as f:
                f.write(base64.b64decode(b64_data))

            return {"file_url": f"mediafiles/files/{filename}", "file_name": filename, "file_uuid": str(uuid.uuid4())}
        except Exception as e:
            return {"error": str(e)}
