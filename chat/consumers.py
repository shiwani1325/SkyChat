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
from .models import EmployeeChat as EmployeeChatModel
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
        self.manually_disconnected = False

    async def connect(self):
        self.sender_id = self.scope['url_route']['kwargs']['sender_id']
        self.receiver_id = self.scope['url_route']['kwargs']['receiver_id']
        self.emp_room_group_name = f'emp_room_{min(self.sender_id, self.receiver_id)}_{max(self.sender_id, self.receiver_id)}'
        await self.channel_layer.group_add(self.emp_room_group_name, self.channel_name)
        EmployeeChat.ACTIVE_USERS[self.sender_id] = self.emp_room_group_name
        await add_active_user(self.sender_id, self.emp_room_group_name)

        await self.broadcast_status_to_contacts(self.sender_id,'online')
        await self.accept()
        await self.mark_all_messages_read(self.sender_id,self.receiver_id)

    async def disconnect(self, close_code):
        if not self.manually_disconnected:
            await remove_active_user(self.sender_id)
            await self.channel_layer.group_discard(self.emp_room_group_name, self.channel_name)
            await self.broadcast_status_to_contacts(self.sender_id, 'offline')

    @database_sync_to_async
    def set_user_online(self, user_id):
        try:
            emp = TMEmployeeDetail.objects.get(id=user_id)
            emp.is_online = True
            emp.save(update_fields = ['is_online'])
        except TMEmployeeDetail.DoesNotExist:
            pass

    @database_sync_to_async
    def set_user_offline(self, user_id):
        try:
            emp = TMEmployeeDetail.objects.get(id=user_id)
            emp.is_online = False
            emp.last_seen = datetime.now()
            emp.save(update_fields = ['is_online','last_seen'])
        except TMEmployeeDetail.DoesNotExist:
            pass


    @database_sync_to_async
    def get_user_contact(self, user_id):
        chats = EmployeeChatModel.objects.filter(
            Q(sender_id=user_id) | Q(receiver_id=user_id)
        ).values_list('sender_id', 'receiver_id')

        contact_ids = set()
        for sid, rid in chats:
            if sid != user_id:
                contact_ids.add(sid)
            if rid != user_id:
                contact_ids.add(rid)
        return list(contact_ids)


    async def broadcast_status_to_contacts(self, user_id, status):
        contacts = await self.get_user_contact(user_id)
        last_seen = datetime.now().isoformat()
        for contact_id in contacts:
            room_name = f'emp_room_{min(str(user_id), str(contact_id))}_{max(str(user_id), str(contact_id))}'
            await self.channel_layer.group_send(
                room_name,
                {
                    'type': 'user_status_update',
                    'user_id': user_id,
                    'status': status,
                    'last_seen': last_seen
                }
            )

    
    async def mark_all_messages_read(self, connected_user_id, chat_partner_id):
        from .models import EmployeeChat
        try:
            chats_q = await database_sync_to_async(EmployeeChat.objects.filter)(
                Q(sender__id=connected_user_id, receiver__id=chat_partner_id) | 
                Q(sender__id=chat_partner_id, receiver__id=connected_user_id)
            )
            chats = await database_sync_to_async(list)(chats_q)

            updated_messages = []
            for chat in chats:
                modified = False
                for msg in chat.messages:
                    # print(f"msg :{msg}")
                    if str(msg.get('receiver')) == str(connected_user_id) and not msg.get('read', True):
                        msg['read'] = True
                        msg['status']="seen"
                        modified = True
                        # updated_messages.append(msg)
                        updated_messages.append({
                            "message_id":msg.get('message_id'),
                            "status":"seen",
                            "read":True
                        })

                if modified:
                    await database_sync_to_async(setattr)(chat, 'messages', chat.messages)
                    await database_sync_to_async(chat.save)(update_fields=['messages'])

            if updated_messages:
                emp_room_group_name = f'emp_room_{min(str(connected_user_id), str(chat_partner_id))}_{max(str(connected_user_id), str(chat_partner_id))}'
                await self.channel_layer.group_send(
                    # f'user_{chat_partner_id}',
                    emp_room_group_name,
                    {
                        'type':'messages_seen_ack',
                        'updated_messages':updated_messages,
                        'by_user':connected_user_id
                    }
                )
        except Exception as e:
            print(f'[Error in mark_all_messages_read]: {e}')


    async def messages_seen_ack(self, event):
        for msg in event['updated_messages']:
            if 'content' in msg and msg['content']:
                keys = load_keys()
                if keys:
                    cipher_suite=Fernet(keys[-1])
                    msg['content'] = cipher_suite.decrypt(msg['content'].encode()).decode()
        await self.send(text_data=json.dumps({
            'type':'messages_read',
            'updated_messages':event['updated_messages'],
            'seen_by':event['by_user']
        }))


    async def user_status_update(self, event):
        # print(f"userstatusupdate")
        try:
            await self.send(text_data = json.dumps({
                'type':'user_status_update',
                'user_id':event['user_id'],
                'status': event['status'],
                'last_seen':event['last_seen']
            }))
        except Exception as e:
            print(f"user status update error :{e}")


    async def typing_status(self, event):
        try:
            await self.send(text_data=json.dumps({
                'type':'typing_status',
                'user_id':event['user_id'],
                'status':event['status']
            }))
        except Exception as e:
            print(f"user status typing error :{e}")


    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        sender_id = data.get('sender')
        receiver_ids = data.get('receiver', [])
        message_type = data.get('type', 'message')
        message_content = data.get('content')
        media_files = data.get('file', [])
        replied_to = data.get('replied_to')
        forwarded_content = data.get('forwarded_content', [])

        if data.get('type') == 'user_typing':
            await self.channel_layer.group_send(
                self.emp_room_group_name,{
                    'type':'typing_status',
                    'user_id':sender_id,
                    'status':'typing...'
                }
            )
        elif data.get('type') == 'user_online':
            await self.channel_layer.group_send(
                self.emp_room_group_name,
                {
                    'type':'typing_status',
                    'user_id':sender_id,
                    'status':'online'
                }
            )

        
        if data.get('type') == "disconnect_request":
            self.manually_disconnected=True
            await self.set_user_offline(sender_id)
            await self.channel_layer.group_discard(self.emp_room_group_name, self.channel_name)
            await remove_active_user(sender_id)

            still_active = await get_user_room(sender_id) 
            if not still_active:
                await self.channel_layer.group_send(
                    self.emp_room_group_name,
                    {
                        'type':'user_status_update',
                        'user_id':sender_id,
                        'status':'offline',
                        'last_seen':datetime.now().isoformat()
                    }
                )
            await self.close()
            return 

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

        sender_obj, sender_name = await self.get_employee_and_name(sender_id)
        message_id = str(uuid.uuid4())

        # preview_message = {
        #     'type': 'chat_message',
        #     'sender_id': sender_id,
        #     'receiver_id': receiver_ids[0] if receiver_ids else "",
        #     'sender_name': sender_name,
        #     'receiver_name': '',
        #     'content': message_content,
        #     'file': media_files,
        #     'message_id': message_id,
        #     'status': 'sending',
        #     'Activity': 'Sending...',
        #     'timestamp': datetime.now().isoformat(),    
        #     'message_type': message_type
        # }
        # await self.send(text_data=json.dumps(preview_message, ensure_ascii=False))

# changes done here for status part before sent passing static   24-07-2025

        async def process_receiver(receiver_id):
            try:
                receiver_obj, receiver_name = await self.get_employee_and_name(receiver_id)
                receiver_room = await get_user_room(receiver_id)
                # print(f"receiver room :{receiver_room}")
                expected_room = f'emp_room_{min(sender_id, receiver_id)}_{max(sender_id, receiver_id)}'
                # print(f"expected room :{expected_room}")
                read = receiver_room == expected_room
                # print(f"read:{read}")
                status = "seen" if read else "sent"
                message_data = await self.save_chat_message(
                    sender_id, receiver_id,
                    sender_name, receiver_name,
                    encrypted_content, files_info, message_id, #"sent"
                    status, read,
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
            # message['replied_to'] = replied_to
            if 'file' in replied_to and replied_to['file']:
                formatted_file=[]
                for file_f in replied_to['file']:
                    formatted_file.append({'file_url':file_f.strip()})
                replied_to['file']=formatted_file
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
            if ext not in ['jpg', 'jpeg', 'png', 'pdf', 'txt', 'docx', 'xls', 'xlsx', ]:
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


    # deleted message on socket

    async def message_delete(self, event):
        await self.send(text_data=json.dumps({
            "type":"message_delete",
            "message_id":event['message_id'],
            "delete_type":event['delete_type'],
            "sender_id":event['sender_id'],
            "receiver_id":event['receiver_id']
        }))


    async def VideoSharing(self, event):
        await self.send(text_data = json.dumps({
            'type':"VideoSharing",
            "message_id" :event['message_id'],
            "sender_id":event['sender_id'],
            "receiver_id":event['receiver_id'],
            "sender_name":event['sender_name'],
            "receiver_name":event["receiver_name"],
            "file":event['file'],
            "status":"sent"
        }))
        