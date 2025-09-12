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
from groupchat.models import EmployeeGroup, EmployeeGroupChat
from groupchat.serializers import EmployeeGroupChatSerializer
import asyncio
import os
import uuid
import base64
from cryptography.fernet import Fernet
from django.conf import settings
from django.db.models import Q
from datetime import datetime


# receiver_emp_id = login user id
class EmployeeList1(AsyncWebsocketConsumer):
    async def connect(self):
        # self.employee_mail = self.scope['url_route']['kwargs']['employee_mail']
        await self.accept()
        self.keep_sending = True
        asyncio.create_task(self.periodic_update())
    
    async def disconnect(self, close_code):
        self.keep_sending = False


    async def receive(self, text_data):
        # employee_mail = request.query_params.get('employee_mail')
        # self.employee_mail = request.query_params.get('employee_mail')
        request_data = json.loads(text_data)
        self.employee_email = request_data.get('employee_mail') 
        employee_mail = request_data.get('employee_mail')

        try:
            employee = await self.get_employee(employee_mail)
            org_id, emp_id=employee['org_id'], employee['emp_id']
            # print(f"org_id:{org_id} & emp_id :{emp_id}")
            unread_count = await sync_to_async(self.get_unread_notifications_count)(emp_id)
            unread_map = unread_count.get("unread_per_sender", {}) if unread_count else {}

            if org_id is None:
                emp_data = []
            else:
                emp_data = await self.employee_list(org_id, emp_id, unread_map)
                # print(f"empData are :{emp_data}")
            
            await self.send(text_data=json.dumps({
                "notification_data":unread_count,
                "emp_data":emp_data,
            }, ensure_ascii=False))
            
            
        except User.DoesNotExist:
            await self.send(text_data=json.dumps({
                "Status": "Error",
                "message": "Employee not found"
            }))


    async def periodic_update(self):
        while self.keep_sending:
            try:
                if hasattr(self, "employee_email"):
                    employee = await self.get_employee(self.employee_email)
                    # print(f"employee in periodic update:{employee}")
                    org_id, emp_id = employee["org_id"], employee["emp_id"]
                    unread_count = await sync_to_async(self.get_unread_notifications_count)(emp_id)
                    unread_map = unread_count.get("unread_per_sender", {}) if unread_count else {}
                    emp_data = await self.employee_list(org_id, emp_id, unread_map) if org_id else []

                    await self.send(text_data=json.dumps({
                        "notification_data": unread_count,
                        "emp_data": emp_data,
                    }, ensure_ascii=False))
            except Exception as e:
                print(f"[Error] periodic_update: {e}")

            await asyncio.sleep(1)


    async def employee_list(self, org_id, receiver_emp_id, unread_map):
        rows = []

        # This code is for employee room list ---------------------     Employee---------------------------------------
        org_employee_list = await sync_to_async(list)(
            User.objects.select_related('role').filter(org_id=org_id)
        )
        serializer = UserSerializer(org_employee_list, many=True)
        for item in serializer.data:
            # print(f"for loop")
            emp_id = item.get("emp_id")
            # print(f"emp_id:{emp_id}")
            if not emp_id:
                continue

            emp_details = await self.get_employee_details(emp_id)
            # print(f"emp_details:{emp_details}")
            # me_user = emp_details['UserEmail']
            # if self.employee_email == me_user:
            #     emp_name = emp_details['EmployeeName']+" "+ "(Me)"
            
            # else:
            #     emp_name = None
            emp_details["unread_count_from_sender"] = unread_map.get(str(emp_id), 0)

            # fetch latest message and attach a sortable timestamp
            latest_msg = None
            # latest_ts  = ""  # empty string sorts after real timestamps
            latest_ts = str(emp_details.get('CreatedOn',''))
            try:
                latest_msg = await self.get_latest_message(emp_id, receiver_emp_id)
                if latest_msg:
                    latest_ts = latest_msg.get("timestamp", "")
            except Exception as e:
                print(f"Error fetching latest message for emp_id {emp_id}: {e}")
            
            # emp_details['emp_name'] = emp_name
            emp_details["latest_message"] = latest_msg
            emp_details["_latest_ts"]     = latest_ts  # helper field for sorting
            rows.append(emp_details)
            # print(f"rows:{rows}")


        # For Group Chat Room -----------------------------------------------------   Group ---------------------------------------------------
        # group_list = await sync_to_async(list)(
        #     EmployeeGroup.objects.filter(memberships__user__id=receiver_emp_id)
        # )
        # # print(f"group_list:{group_list}")
        # # group_latest_message=None
        # for group in group_list: 
        #     latest_msg=None

        #     # if not group_latest_message:
        #     # print(f"group:{group.id}")
        #     latest_ts = group.created_on.isoformat()
        #     # print(f"_latest_ts:{latest_ts}")
        #     try:
        #         latest_msg = await self.get_latest_message_group(emp_id, group)
        #         # print(f"latest message after latest message griup completed :{latest_msg}")
        #         if latest_msg:
        #             latest_ts = latest_msg.get("timestamp",group.created_on.isoformat())
        #             # print(f"latest_ts:{latest_ts}")
        #     except Exception as e:
        #         print(f"Error fetching latest message for emp_id {emp_id}: {e}")


        #     group_data = {
        #         "id":group.id,
        #         "type":"Group",
        #         "GroupName":group.groupname,
        #         "Description":group.description,
        #         # "created_on":group.created_on.isoformat(),
        #         "latest_message":latest_msg if latest_msg else None,
        #         "_latest_ts":latest_ts

        #     }
        #     # print(f"group data:{group_data}")
        #     rows.append(group_data)
            

        # -------- sort: newest timestamp first -----------
        # print(f"rows all data :{rows}")
        rows.sort(key=lambda r: r["_latest_ts"], reverse=True)

        # remove helper field before returning
        for r in rows:
            # print(f"r :{r}")
            r.pop("_latest_ts", None)

        return rows


    @database_sync_to_async
    def get_employee(self, employee_mail):
        data = User.objects.get(email=employee_mail)
        # print(f"data :{data}")
        return UserSerializer(data).data

    @database_sync_to_async
    def get_employee_details(self, emp_id):
        emp_data = TMEmployeeDetail.objects.get(id=emp_id)
        # print(f"emp_data:{emp_data}")
        return EmployeeSerializers(emp_data).data
        
    @database_sync_to_async
    def get_latest_message(self, emp_id, receiver_emp_id):
        try:
            # ▸ 1. fetch the chat object that contains the most‑recent timestamp
            chat = (
                EmployeeChat.objects
                .filter(
                    Q(sender=emp_id,        receiver=receiver_emp_id) |
                    Q(sender=receiver_emp_id, receiver=emp_id)
                )
                .order_by("-timestamp")
                .first()
            )
            if not chat or not chat.messages:
                return None

            # ▸ 2. pick the newest embedded message
            latest_msg = sorted(
                chat.messages,
                key=lambda m: m.get("timestamp", ""),
                reverse=True
            )[0]

            # ▸ 3. decrypt / mark deleted
            if latest_msg.get("deleted", False):
                plaintext = "Deleted Message"
            else:
                ciphertext = latest_msg.get("content", "")
                plaintext  = ciphertext
                for key in self.load_key():
                    try:
                        trial = self.decrypt_message(ciphertext, key)
                        # print(f"trial in one to one chat:{trial}")
                        if trial is not None:
                            plaintext = trial
                            # print(f"plain text in one to one chat :{plaintext}")
                            break
                    except Exception:
                        continue  # try next key

            latest_msg["content"] = plaintext

            

            # ▸ 4. return the reduced dict expected by your frontend
            return {
                "sender":        latest_msg.get("sender"),
                "sender_name":   latest_msg.get("sender_name"),
                "receiver":      latest_msg.get("receiver"),
                "receiver_name": latest_msg.get("receiver_name"),
                "timestamp":     latest_msg.get("timestamp"),
                "content":       latest_msg.get("content"),
                "file":          latest_msg.get("file",[]),
                "read":          latest_msg.get("read", False),
            }

        except Exception as e:
            # print(f"Error inside get_latest_message: {e}")
            return None

    @database_sync_to_async
    def get_latest_message_group(self, emp_id, group):
        latest_group_chat = EmployeeGroupChat.objects.filter(group=group).order_by("-timestamp").first()
        # print(f"groupchat:{latest_group_chat}")
        if not latest_group_chat:
            return None
        serializer = EmployeeGroupChatSerializer(latest_group_chat)
        chat_data = dict(serializer.data)
        # print(f"chat_data:{chat_data}")
        # print(f"serializer chat data:{serializer.data}")
        ciphertext = chat_data['content']
        plaintext = ciphertext
        # print(f"ciphertext:{ciphertext}")
        # print(f"plain text : {plaintext}")
        for key in self.load_key():
            try:
                trial = self.decrypt_message(ciphertext, key)
                # print(f"trial :{trial}")
                if trial is not None:
                    plaintext=trial
                    # print(f"text in trial not None;{plaintext}")
                    break
            except Exception:
                continue
        chat_data['content']=plaintext
        # print(f"serilaizer updated text:{chat_data['content']}")
        
        return {
            "sender": chat_data['sender'] ,
            "group_id":chat_data['group'] ,
            "timestamp":     chat_data['timestamp'],
            "content": chat_data['content'], 
            # "file":          serializer.data['file', None],
            "read": False

        }

        # print(f"serializer message :{serializer.data['content']}")
        # return 

        





    def get_unread_notifications_count(self, emp_id):
        keys = self.load_key()
        unread_messages=[]
        unread_messages_by_sender = defaultdict(lambda:{"unread_count_sender":0,"messages":[]})
        unread_count=0
        chats = EmployeeChat.objects.filter(Q(receiver_id = emp_id)| Q(messages__icontains = emp_id))
        # print(f"chats:{chats}")

        if not chats.exists:
            return {
            "receiver": emp_id,
            "unread_count": 0,
            "unread_sender": 0,
            "unread_messages": [],
            "unread_per_sender": {}       
        }

        for chat in chats:
            # print(f"chat from unread notifications:{chat}")
            for msg in chat.messages:
                # print(f"msg are :{msg}")
                if str(msg.get('receiver')) == str(emp_id)  and not msg.get('read',False):
                    unread_count+=1
                    sender_id = str(msg.get('sender'))

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

                    msg['content'] = decrypted_content
                    unread_messages_by_sender[sender_id]['unread_count_sender']+=1
                    unread_messages_by_sender[sender_id]['messages'].append(msg)
                    unread_messages.append(msg)

        
            
        unread_count = len(unread_messages)
        # print(f"unread count:{unread_count}")
        formatted_unread_messages=[
            {"sender":sender, "receiver":emp_id, **data} for sender,data in unread_messages_by_sender.items()
        ]

        return {
            "receiver":emp_id,
            "unread_count":unread_count,
            "unread_sender":len(unread_messages_by_sender),
            "unread_messages":formatted_unread_messages,
            "unread_per_sender": {sender:data["unread_count_sender"] for sender, data in unread_messages_by_sender.items()}
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
            # print(f"fernet :{fernet}")
            return fernet.decrypt(encrypted_content.encode()).decode()
        except:
            return None