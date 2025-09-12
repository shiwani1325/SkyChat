# groupchat/consumers.py
import json
import uuid
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from cryptography.fernet import Fernet
from django.contrib.auth import get_user_model
from employee.models import TMEmployeeDetail
from .models import EmployeeGroup, EmployeeGroupMember, EmployeeGroupChat, MessageStatus
from chat.utils import generate_and_save_key, load_keys  # reuse your encryption utils

User = get_user_model()


class GroupChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.key = None
        self.group_id = None
        self.sender_id = None
        self.group_room_name = None

    async def connect(self):
        """On websocket connect"""
        self.group_id = self.scope['url_route']['kwargs']['group_id']
        self.sender_id = self.scope['url_route']['kwargs']['sender_id']
        self.group_room_name = f"group_room_{self.group_id}"

        await self.channel_layer.group_add(self.group_room_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_room_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        """Receive message from WebSocket"""
        data = json.loads(text_data)
        sender_id = data.get("sender")
        content = data.get("content")
        message_type = data.get("type", "message")  # only "message" for now

        # 🔐 Encryption (same as your 1-1 chat)
        generate_and_save_key()
        keys = load_keys()
        if not keys:
            return await self.send(text_data=json.dumps({"error": "Encryption key not found"}))

        self.key = keys[-1]
        cipher_suite = Fernet(self.key)
        encrypted_content = cipher_suite.encrypt(content.encode()).decode()

        # unique message ID
        message_id = str(uuid.uuid4())
        print(f"messageID:{message_id}")

        # save message
        message_data = await self.save_group_message(
            self.group_id, sender_id, encrypted_content, message_id, message_type
        )

        print(f"Message data :{message_data}")
        # broadcast to group members
        await self.channel_layer.group_send(
            self.group_room_name,
            {
                **message_data,
                "type": "chat_message",
                "timestamp": datetime.now().isoformat(),
            }
        )

    async def chat_message(self, event):
        """Send decrypted message to WebSocket"""
        keys = load_keys()
        if not keys:
            return await self.send(text_data=json.dumps({"error": "Key missing"}))

        self.key = keys[-1]
        cipher_suite = Fernet(self.key)
        decrypted_content = cipher_suite.decrypt(event["content"].encode()).decode()

        # 🔥 Response format SAME as 1-1 chat
        response = {
            "type": "chat_message",
            "sender_id": event["sender_id"],
            "sender_name": event["sender_name"],
            "group_id": event["group_id"],
            "content": decrypted_content,
            "message_id": event["message_id"],
            "status": event["status"],
            "timestamp": event["timestamp"],
            "message_type": event["message_type"]
        }
        await self.send(text_data=json.dumps(response, ensure_ascii=False))

    # ---------------- DB ----------------
    @database_sync_to_async
    def save_group_message(self, group_id, sender_id, content, message_id, message_type):
        group = EmployeeGroup.objects.get(id=group_id)
        employee = TMEmployeeDetail.objects.get(id=sender_id)   # TMEmployeeDetail
        print(f'employee :{employee.id}')
        sender_user = User.objects.get(emp_id=employee)
        # sender = TMEmployeeDetail.objects.get(id=sender_id)
        print(f"sender :{sender_user}")

        chat = EmployeeGroupChat.objects.create(
            group=group,
            sender=employee,  # because sender is TMEmployeeDetail, link to User
            content=content,
            message_type=message_type
        )
        print(f"chat:{chat}")

        # create MessageStatus entries for each member
        members = EmployeeGroupMember.objects.filter(group=group)
        print(f"members:{members}")
        for m in members:
            print(f"m:{m}")
            # m.user → TMEmployeeDetail
            try:
                member_user = User.objects.get(emp_id=m.user)   # map employee → user
                print(f"member_user:{member_user}")
            except User.DoesNotExist:
                continue  # skip if no user found for this employee
            print(f"message before create")
            MessageStatus.objects.create(
                message=chat,
                user=m.user,
                delivered=True if str(m.user.id) != str(sender_id) else True,
                delivered_at=datetime.now(),
                read=(str(m.user.id) == str(sender_id)),  #sender auto-reads
                read_at=datetime.now() if str(m.user.id) == str(sender_id) else None,
            )
            print(f"Message after save ")

        return {
            "sender_id": sender_id,
            "sender_name": employee.EmployeeName,
            "group_id": group_id,
            "content": content,
            "message_id": message_id,
            "status": "sent",
            "message_type": message_type,
        }
