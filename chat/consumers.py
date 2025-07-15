import json
import os
import uuid
import base64
import asyncio
from cryptography.fernet import Fernet
from django.conf import settings
from django.db.models import Q
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from datetime import datetime
from employee.models import TMEmployeeDetail
from .utils import generate_and_save_key, load_keys, add_active_user, remove_active_user, get_user_room


class WebsocketConnectRoom(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass


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
        EmployeeChat.ACTIVE_USERS[self.sender_id] = self.emp_room_group_name
        # print(f"sender id is:{self.sender_id} and receiver id is :{self.receiver_id}")
        # print(f"Room created:{self.emp_room_group_name}")

        # await add_active_user(self.sender_id, self.emp_room_group_name)
        await self.channel_layer.group_add(self.emp_room_group_name, self.channel_name)
        await self.accept()

        # receiver_room = await get_user_room(self.receiver_id)
        # # print(f"Receiver room from Redis: {receiver_room}")
        # # print(f"Current emp_room_group_name: {self.emp_room_group_name}")
        # if receiver_room == self.emp_room_group_name:
        #     await self.mark_all_messages_read(self.receiver_id, self.sender_id)

    async def disconnect(self, close_code):
        await remove_active_user(self.sender_id)
        await self.channel_layer.group_discard(self.emp_room_group_name, self.channel_name)

    async def mark_all_messages_read(self, receiver_id, sender_id):
        from .models import EmployeeChat as EmployeeChatModel
        try:
            chats = await database_sync_to_async(list)(EmployeeChatModel.objects.filter(
                Q(sender__id=sender_id, receiver__id=receiver_id) |
                Q(sender__id=receiver_id, receiver__id=sender_id)
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
                    await database_sync_to_async(setattr)(chat, "messages", chat.messages)
                    await database_sync_to_async(chat.save)(update_fields=["messages"])

            if updated_messages:
                await self.channel_layer.group_send(
                    self.emp_room_group_name,
                    {'type': "updating_existing_message", "updated_messages": updated_messages}
                )
        except Exception as e:
            print(f"Error in mark_all_messages_read: {e}")

    async def updating_existing_message(self, event):
        for msg in event["updated_messages"]:
            await self.update_message_in_cache(msg)

    async def update_message_in_cache(self, updated_msg):
        keys = load_keys()
        if not keys:
            return

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
        # print(f"data receive ;{data}")

        for each_forwarded_content in forwarded_content:
            message_id= str(uuid.uuid4())
            each_forwarded_content['message_id']=message_id
            each_forwarded_content['timestamp'] = datetime.now().isoformat()


        generate_and_save_key()
        keys = load_keys()
        if not keys:
            return await self.send(text_data=json.dumps({"error": "Encryption key not found"}))

        self.key = keys[-1]
        cipher_suite = Fernet(self.key)
        encrypted_content = cipher_suite.encrypt(message_content.encode()).decode() if message_content else None


        files_info = await asyncio.gather(*(self.save_uploaded_file(f, sender_id) for f in media_files))
        # print(f"file info :{files_info}")

        sender_obj, sender_name = await self.get_employee_and_name(sender_id)
        message_id = str(uuid.uuid4())

        preview_message = {
            'type': 'chat_message',
            'sender': sender_id,
            'receiver': receiver_ids[0] if receiver_ids else "",
            'sender_name': sender_name,
            'receiver_name': '',
            'content': message_content,
            'file': media_files,
            'message_id': message_id,
            'status': 'sending',
            'Activity': 'Sending...',
            'timestamp': datetime.now().isoformat(),    
            'message_type': message_type
        }
        await self.send(text_data=json.dumps(preview_message, ensure_ascii=False))

        async def process_receiver(receiver_id):
            try:
                receiver_obj, receiver_name = await self.get_employee_and_name(receiver_id)
                receiver_room = await get_user_room(receiver_id)
                expected_room = f'emp_room_{min(sender_id, receiver_id)}_{max(sender_id, receiver_id)}'
                read = receiver_room == expected_room

                message_data = await self.save_chat_message(
                    sender_id, receiver_id,
                    sender_name, receiver_name,
                    encrypted_content, files_info, message_id, "sent", read,
                    message_type, replied_to, forwarded_content
                )


                emp_room_group_name = f'emp_room_{min(sender_id, receiver_id)}_{max(sender_id, receiver_id)}'

                await self.channel_layer.group_send(
                    emp_room_group_name,
                    {
                        **message_data,
                        'type': 'chat_message',
                        'timestamp': datetime.now().isoformat(),
                        'Activity': "Online" if read else "Offline"
                    }
                )
            except Exception as e:
                print(f"[Receiver Processing Error]: {e}")

        await asyncio.gather(*(process_receiver(rid) for rid in receiver_ids))

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
        from employee.models import TMEmployeeDetail

        sender, receiver = sorted(
            [TMEmployeeDetail.objects.get(id=sender_id),
             TMEmployeeDetail.objects.get(id=receiver_id)],
            key=lambda emp: emp.id
        )

        chat_obj, _ = EmployeeChatModel.objects.get_or_create(sender=sender, receiver=receiver)
        # print(f"Chatobj:{chat_obj}")

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

    @database_sync_to_async
    def get_employee_and_name(self, employee_id):
        employee = TMEmployeeDetail.objects.get(id=employee_id)
        return employee, employee.EmployeeName

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

            return {
                "file_url": f"mediafiles/files/{filename}",
                "file_name": filename,
                "file_uuid": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e)}
