import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from datetime import datetime
import asyncio
import os
import uuid
import base64
from cryptography.fernet import Fernet
from django.conf import settings
from django.db.models import Q
import re
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
        self.emp_room_group_name = f'emp_room_group_name{min(self.sender_id, self.receiver_id)}_{max(self.sender_id, self.receiver_id)}'
        self.__class__.ACTIVE_USERS[self.sender_id] = self.emp_room_group_name

        await self.channel_layer.group_add(
            self.emp_room_group_name,
            self.channel_name
        )
        await self.accept()

        if self.sender_id in self.__class__.ACTIVE_USERS and self.receiver_id in self.__class__.ACTIVE_USERS:
            if self.__class__.ACTIVE_USERS[self.receiver_id] == self.emp_room_group_name:
                await sync_to_async(self.mark_all_messages_read)(self.receiver_id, self.sender_id)
                
    async def disconnect(self, close_code):
        if self.sender_id in self.__class__.ACTIVE_USERS:
            del self.__class__.ACTIVE_USERS[self.sender_id]

        await self.channel_layer.group_discard(
            self.emp_room_group_name,
            self.channel_name
        )

    def mark_all_messages_read(self, receiver_id, sender_id):
        from .models import EmployeeChat

        try:
            chats = EmployeeChat.objects.filter(
                Q(sender__employee_id=sender_id, receiver__employee_id=receiver_id) |
                Q(sender__employee_id=receiver_id, receiver__employee_id=sender_id)
            )
            updated_messages = []
            modified_message = False

            for chat in chats:
                each_chat = chat.messages
                for msg in each_chat:
                    if not msg.get("read", True):
                        msg["read"] = True
                        updated_messages.append(msg)
                        modified_message = True

                if modified_message:
                    chat.messages = each_chat
                    chat.save(update_fields=["messages"])

            if modified_message:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    self.emp_room_group_name, {
                        'type': "updating_existing_message",
                        "updated_messages": updated_messages
                    }
                )

        except Exception as e:
            print(f"Error in mark_all_messages_read: {str(e)}")

    async def updating_existing_message(self, event):
        updated_messages = event["updated_messages"]
        for updated_message in updated_messages:
            await self.send(text_data=json.dumps({
                "type": "message_update",
                "updated_message": updated_message
            }))
            await self.update_message_in_cache(updated_message)

    async def update_message_in_cache(self, updated_message):
        keys = load_keys()  # Updated line
        if not keys:
            return

        self.key = keys[-1]
        cipher_suite = Fernet(self.key)

        decrypted_text = None
        if updated_message['content']:
            decrypted_text = cipher_suite.decrypt(updated_message['content'].encode()).decode()

        updated_message['content'] = decrypted_text

        await self.send(text_data=json.dumps({
            "type": "message_update",
            "updated_message": updated_message
        }))

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        message_type = data.get('type', 'message')
        sender_id = data.get('sender')
        receiver_ids = data.get('receiver', [])
        message_content = data.get('content')
        media_file = data.get('file', [])
        replied_to = data.get('replied_to')
        forwarded_content = data.get('forwarded_content', [])
        # print(f"forwarded content :{forwarded_content}")

        for each_forwarded_content in forwarded_content:
            message_id = str(uuid.uuid4())
            each_forwarded_content["message_id"] = message_id

        generate_and_save_key()  # Updated line
        keys = load_keys()  # Updated line
        if not keys:
            await self.send(text_data=json.dumps({"error": "No encryption keys found."}))
            return

        self.key = keys[-1]
        cipher_suite = Fernet(self.key)

        cipher_encrypted_text = None
        if message_content:
            text_message = bytes(message_content, 'utf-8')
            cipher_encrypted_text = cipher_suite.encrypt(text_message).decode('utf-8')

        files_info = []
        if media_file:
            for each_file in media_file:
                file_url, file_uuid = await self.save_uploaded_file(each_file, sender_id)
                match = re.search(r'_(.+)', file_url)
                extracted_name = match.group(1) if match else None
                files_info.append({"file_url": file_url, "file_name": extracted_name, "file_uuid": file_uuid})

        status = "sent"
        sender_employee_name = await database_sync_to_async(Employee.objects.get)(employee_id=sender_id)

        for receiver_id in receiver_ids:
            message_id = str(uuid.uuid4())
            read = False
            Activity = "Online" if self.sender_id in self.__class__.ACTIVE_USERS and receiver_id in self.__class__.ACTIVE_USERS else "Offline"
            emp_room_group_name = f'emp_room_group_name{min(self.sender_id, receiver_id)}_{max(self.sender_id, receiver_id)}'
            if self.sender_id in self.__class__.ACTIVE_USERS and receiver_id in self.__class__.ACTIVE_USERS:
                if self.__class__.ACTIVE_USERS[receiver_id] == emp_room_group_name:
                    read = True

            receiver_employee_name = await database_sync_to_async(Employee.objects.get)(employee_id=receiver_id)

            try:
                message_data = await self.save_chat_message(
                    sender_id,
                    receiver_id,
                    sender_employee_name.name,
                    receiver_employee_name.name,
                    cipher_encrypted_text,
                    files_info,
                    message_id,
                    status,
                    read,
                    message_type=message_type,
                    replied_to=replied_to,
                    forwarded_content=forwarded_content
                )
            except Exception as e:
                await self.send(text_data=json.dumps({"error": str(e)}))
                return

            message_data = {
                'type': 'chat_message',
                'message_type': message_type,
                'content': cipher_encrypted_text,
                'sender': sender_id,
                'receiver': receiver_id,
                'sender_name': sender_employee_name.name,
                'receiver_name': receiver_employee_name.name,
                'file': files_info,
                'timestamp': datetime.now().isoformat(),
                'message_id': message_id,
                'Activity': Activity,
                'status': status,
                'read': read
            }

            if message_type == 'reply' and replied_to:
                message_data['replied_to'] = replied_to

            elif message_type == 'forward' and forwarded_content:
                message_data['forwarded_content'] = forwarded_content

            await self.channel_layer.group_send(
                emp_room_group_name,
                message_data
            )

    async def chat_message(self, event):
        keys = load_keys()  # Updated line
        if not keys:
            await self.send(text_data=json.dumps({"error": "No encryption keys found."}))
            return

        is_read = await self.check_message_status(event['message_id'])
        status = "read" if is_read else event['status']

        self.key = keys[-1]
        cipher_suite = Fernet(self.key)

        decrypted_text = None
        if event['content']:
            decrypted_text = cipher_suite.decrypt(event['content'].encode()).decode()

        response_data = {
            'message_type': event['message_type'],
            'sender': event['sender'],
            'receiver': event['receiver'],
            'sender_name': event['sender_name'],
            'receiver_name': event['receiver_name'],
            'content': decrypted_text,
            'file': event['file'],
            'timestamp': event['timestamp'],
            'message_id': event['message_id'],
            'Activity': event['Activity'],
            'status': status,
            'read': event['read'],
        }

        if event['message_type'] == 'reply' and 'replied_to' in event:
            response_data['replied_to'] = event['replied_to']

        elif event['message_type'] == 'forward' and 'forwarded_content' in event:
            response_data['forwarded_content'] = event['forwarded_content']

        await self.send(text_data=json.dumps(response_data, ensure_ascii=False))

    @database_sync_to_async
    def check_message_status(self, message_id):
        from .models import EmployeeChat

        try:
            chat = EmployeeChat.objects.get(
                messages__contains=[{'message_id': message_id}]
            )

            for message in chat.messages:
                if message.get('message_id') == message_id:
                    return message.get('read', False)
            return False

        except EmployeeChat.DoesNotExist:
            return False

    @database_sync_to_async
    def save_chat_message(self, sender_id, receiver_id, sender_name, receiver_name, content,
                          files_info, message_id, status, read, message_type='message',
                          replied_to=None, forwarded_content=None):
        from .models import EmployeeChat
        from employee.models import Employee

        sender, receiver = sorted(
            [Employee.objects.get(employee_id=sender_id),
             Employee.objects.get(employee_id=receiver_id)],
            key=lambda emp: emp.employee_id
        )

        chat_session, created = EmployeeChat.objects.get_or_create(
            sender=sender,
            receiver=receiver
        )

        message_data = {
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

        if message_type == 'reply' and replied_to:
            message_data['replied_to'] = {
                'message_id': replied_to.get('message_id'),
                'content': replied_to.get('content'),
                'sender': replied_to.get('sender'),
                'sender_name': replied_to.get('sender_name'),
                'timestamp': replied_to.get('timestamp'),
                'file': replied_to.get('file')
            }

        elif message_type == 'forward' and forwarded_content:
            message_data['forwarded_content'] = forwarded_content

        chat_session.add_message(**message_data)
        return message_data

    async def save_uploaded_file(self, each_file, sender_id):
        try:
            format_info, file_data_base64 = each_file.split(';base64,')
            fromat_file_name, other_data = each_file.split('/', 1)
            ext1 = fromat_file_name.split(':')[-1]
            ext2 = format_info.split(':')[1]
            ext = format_info.split('/')[-1]

            if ext not in ['jpg', 'jpeg', 'png', 'pdf', 'txt', 'docx', 'xls', 'xlsx']:
                return None

            base_file_name = f"{sender_id}_{ext1}.{ext}"
            file_data = base64.b64decode(file_data_base64)

            file_directory = os.path.join(settings.MEDIA_ROOT, 'files')
            os.makedirs(file_directory, exist_ok=True)
            file_name = base_file_name

            file_path = os.path.join(file_directory, file_name)
            counter = 1

            while os.path.exists(file_path):
                file_name = f"{sender_id}_{ext1}_{counter}.{ext}"
                file_path = os.path.join(file_directory, file_name)
                counter += 1

            with open(file_path, 'wb') as file:
                file.write(file_data)

            file_uuid = str(uuid.uuid4())
            file_url = f"mediafiles/files/{file_name}"
            return file_url, file_uuid

        except Exception as e:
            return str(e)

