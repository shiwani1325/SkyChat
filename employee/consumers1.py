from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async  
import json
from .models import TMEmployeeDetail
from chat.models import EmployeeChat
from chat.serializers import EmployeeChatSerializer
from .serializers import EmployeeSerializers
from collections import defaultdict
from custom.models import User
from custom.serializers import UserSerializer
import asyncio
import os
import uuid
import base64
from cryptography.fernet import Fernet
from django.conf import settings
from django.db.models import Q
from datetime import datetime


class EmployeeList1(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
    

    async def receive(self, text_data):
        request_data = json.loads(text_data)
        employee_mail = request_data.get('employee_mail')

        try:
            employee = await self.get_employee(employee_mail)
            org_id, emp_id=employee['org_id'], employee['emp_id']
            print(f"org_id:{org_id}")
            print(f"empid in receive:{emp_id}")
            if org_id is None:
                emp_data = []
            else:
                emp_data = await self.employee_list(org_id, emp_id)
            unread_count = await sync_to_async(self.get_unread_notifications_count)(emp_id)

            
            await self.send(text_data=json.dumps({
                # 'count_type': 'unread_count',
                # 'chat_receiver': unread_count['receiver'],
                # 'count': unread_count['unread_count'],
                # "unread_sender_count": unread_count['unread_sender'],
                # 'unread_messages': unread_count['unread_messages'],
                "notification_data":unread_count,
                "emp_data":emp_data,
            }))
            
            
        except User.DoesNotExist:
            await self.send(text_data=json.dumps({
                "Status": "Error",
                "message": "Employee not found"
            }))

    async def employee_list(self, org_id, receiver_emp_id):
        from .serializers import EmployeeSerializers

        org_employee_list = await sync_to_async(list)(User.objects.filter(org_id=org_id))
        serializer = UserSerializer(org_employee_list, many=True)
        latest_chat_employee_list_data=[]
        for item in serializer.data:
            emp_id = item.get('emp_id') 
            print(f"emp id :{emp_id}")
            if emp_id:
                emp_details = await self.get_employee_details(emp_id)
                print(f"emp  details:{emp_details['id']} - {emp_id}")
                try:
                    latest_message = await sync_to_async(lambda : EmployeeChat.objects.filter(Q(sender = emp_id, receiver=receiver_emp_id) | Q(sender=receiver_emp_id, receiver=emp_id)).order_by('-timestamp').first())()
                    print(f"latest messages are :{latest_message}")

                except Exception as e:
                    print(f"Global error in EmployeeList.get: {str(e)}")
        
                latest_chat_employee_list_data.append(emp_details)

        return latest_chat_employee_list_data


    @database_sync_to_async
    def get_employee(self, employee_mail):
        data = User.objects.get(email=employee_mail)
        return UserSerializer(data).data

    @database_sync_to_async
    def get_employee_details(self, emp_id):
        emp_data = TMEmployeeDetail.objects.get(id=emp_id)
        return EmployeeSerializers(emp_data).data
    
    
    # async def send_notifications_update(self):
    #     unread_count = await sync_to_async(self.get_unread_notifications_count)(self.emp_id)
    #     print(f"unread count:{unread_count}")
        # await self.send(text_data=json.dumps({
        #     'count_type': 'unread_count',
        #     'chat_receiver': unread_count['receiver'],
        #     'count': unread_count['unread_count'],
        #     "unread_sender_count": unread_count['unread_sender'],
        #     'unread_messages': unread_count['unread_messages'],
        # }, ensure_ascii=False))
        

    def get_unread_notifications_count(self, emp_id):
        keys = self.load_key()
        unread_messages=[]
        unread_messages_by_sender = defaultdict(lambda:{"unread_count_sender":0,"messages":[]})
        unread_count=0
        chats = EmployeeChat.objects.filter(Q(receiver_id = emp_id)| Q(messages__icontains = emp_id))
        # print(f"chats:{chats}")

        if not chats.exists:
            return None

        for chat in chats:
            # print(f"chat from unread notifications:{chat}")
            for msg in chat.messages:
                # print(f"msg are :{msg}")
                if msg.get('receiver') == emp_id  and not msg.get('read',False):
                    unread_count+=1
                    sender_id = msg.get('sender')

                    if msg.get('deleted',False):
                        decrypted_content = 'Deleted Message'
                    
                    else:
                        encrypted_content = msg.get('content',"")
                        decrypted_content = encrypted_content

                        if encrypted_content and keys:
                            for encryption_key in keys:
                                try:
                                    decrypted_content= self.decrypt_message(encrypted_content,encryption_key)
                                    if decrypted_content is not None:
                                        break
                                    
                                except Exception as e:
                                    print(f"Decryption failed with key {encryption_key} error as :{str(e)}")

                    msg['unread_messages'] = decrypted_content
                    unread_messages_by_sender[sender_id]['unread_count_sender']+=1
                    unread_messages_by_sender[sender_id]['messages'].append(msg)
                    unread_messages.append(msg)
            
            unread_count = len(unread_messages)
            formatted_unread_messages=[
                {"sender":sender, "receiver":emp_id, **data} for sender,data in unread_messages_by_sender.items()
            ]

            return {
                "receiver":emp_id,
                "unread_count":unread_count,
                "unread_sender":len(unread_messages_by_sender),
                "unread_messages":formatted_unread_messages
            }


    def load_key(self):
        import os, base64
        from django.conf import settings
        from cryptography.fernet import Fernet

        key_file_path = os.path.join(settings.BASE_DIR, 'Encryption_Key.key')
        if os.path.exists(key_file_path):
            with open(key_file_path, 'r') as key_file:
                key_base64_list = key_file.readlines()
            return [base64.urlsafe_b64decode(key.strip()) for key in key_base64_list]
        return []

    def decrypt_message(self, encrypted_content, encryption_key):
        from cryptography.fernet import Fernet
        try:
            fernet = Fernet(encryption_key)
            return fernet.decrypt(encrypted_content.encode()).decode()
        except:
            return None