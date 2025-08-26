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
from .models import EmployeeGroupChat, EmployeeGroup
from employee.models import TMEmployeeDetail
from custom.models import User

class GroupEmployeeChat(AsyncWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sender_id = None
        self.group_room_id = None

    async def connect(self):
        self.sender_id = self.scope['url_route']['kwargs']['sender_id']
        self.group_room_id = self.scope['url_route']['kwargs']['group_room_id']
        self.group_room_name = f"group_{self.group_room_id}"
        await self.channel_layer.group_add(self.group_room_name, self.channel_name)
        await self.accept()

    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_room_id, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        await self.save_message(self.group_room_id, self.sender_id, message)

        await self.channel_layer.group_send(
            self.group_room_name,
            {
                'type':'chat_message',
                'sender_id':self.sender_id,
                'message':message
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'sender_id':event['sender_id'],
            'message':event['message'],
        }))

    @database_sync_to_async
    def save_message(self, group_id, sender_id, message):
        group = EmployeeGroup.objects.get(id=group_id)
        sender = User.objects.get(emp_id=sender_id)
        return EmployeeGroupChat.objects.create(group=group, sender=sender, content=message)





