import os
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from cryptography.fernet import Fernet
from django.db.models import F
import base64
from django.conf import settings
from collections import defaultdict
from rest_framework.permissions import AllowAny
from django.db.models import Q
from django.db.models import F, Func, Value, JSONField
from django.db import transaction
from django.db.models import JSONField
from django.utils import timezone
from .models import EmployeeChat, message_backup



class chathistory(APIView):
    permission_classes =[AllowAny]
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
            return f"Error decrypting message: {str(e)}"

    
    def get(self, request):
        keys = self.load_key()
        sender_id  = request.query_params.get("sender_id")
        receiver_id = request.query_params.get("receiver_id")

        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 10))

        if not sender_id:
            return Response(
                {"status": "error", "message": "sender_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = EmployeeChat.objects.all().order_by("-timestamp")
        filtered_data = []
        total_msg_count = 0
        all_msg_index = {}

        def decrypt_content(cipher_text):
            if cipher_text and keys:
                for k in keys:
                    try:
                        plain = self.decrypt_message(cipher_text, k)
                        if "Error decrypting" not in plain:
                            return plain
                    except Exception:
                        continue
            return None

        # Index all messages
        for chat in queryset:
            for m in chat.messages:
                if m.get("message_id"):
                    all_msg_index[m["message_id"]] = m

        for chat in queryset:
            chat_messages = []

            for msg in sorted(chat.messages, key=lambda m: m["timestamp"], reverse=True):
                # Skip deleted
                if sender_id in msg.get("deleted_for", []):
                    continue

                # Filter file deletions
                if isinstance(msg.get("file"), list):
                    msg["file"] = [
                        f for f in msg["file"]
                        if sender_id not in f.get("deleted_for", [])
                    ]

                # Filter forwarded content
                if isinstance(msg.get("forwarded_content"), list):
                    msg["forwarded_content"] = [
                        fc for fc in msg["forwarded_content"]
                        if sender_id not in fc.get("deleted_for", [])
                    ]

                # Check chat between sender and receiver
                if receiver_id:
                    if not ((str(msg["sender"]) == sender_id and str(msg["receiver"]) == receiver_id) or
                            (str(msg["sender"]) == receiver_id and str(msg["receiver"]) == sender_id)):
                        continue
                else:
                    if str(msg["sender"]) != sender_id and str(msg["receiver"]) != sender_id:
                        continue

                # Replied to
                reply_data = None
                replied_to = msg.get("replied_to")
                if isinstance(replied_to, dict):
                    reply_id = replied_to.get("message_id")
                    if reply_id and reply_id in all_msg_index:
                        original = all_msg_index[reply_id]
                        reply_data = {
                            "message_id": original.get("message_id"),
                            "sender": original.get("sender"),
                            "receiver": original.get("receiver"),
                            "sender_name": original.get("sender_name"),
                            "receiver_name": original.get("receiver_name"),
                            "content": decrypt_content(original.get("content")),
                            "timestamp": original.get("timestamp"),
                            "file": original.get("file", [])
                        }

                # Build message structure
                chat_messages.append({
                    "message_id": msg.get("message_id"),
                    "sender": str(msg["sender"]),
                    "receiver": str(msg["receiver"]),
                    "sender_name": msg.get("sender_name"),
                    "receiver_name": msg.get("receiver_name"),
                    "content": decrypt_content(msg.get("content")),
                    "file": msg.get("file", []),
                    "timestamp": msg.get("timestamp"),
                    "read": msg.get("read"),
                    "read_at": msg.get("read_at"),
                    "deleted": msg.get("deleted", False),
                    "deleted_for": msg.get("deleted_for"),
                    "replied_to": reply_data,
                    "forwarded_content": msg.get("forwarded_content"),
                    "message_type": msg.get("message_type", "message"),
                    "status": msg.get("status", "sent")
                })

                total_msg_count += 1

            if chat_messages:
                filtered_data.append({
                    "id": chat.id,
                    "messages": chat_messages
                })

        # Pagination
        total_items = len(filtered_data)
        total_pages = (total_items + page_size - 1) // page_size or 1
        page        = max(1, min(page, total_pages))
        start, end  = (page - 1) * page_size, (page * page_size)
        paged_data  = filtered_data[start:end]

        return Response({
            "status": "success",
            "data": paged_data,
            "pagination": {
                "total_items": total_items,
                "total_pages": total_pages,
                "current_page": page,
                "page_size": page_size,
                "has_next": page < total_pages,
                "has_previous": page > 1
            },
            "total_message_count": total_msg_count,
            "filter_type": "specific_chat" if receiver_id else "all_chats"
        }, status=status.HTTP_200_OK)



    def handle_delete_event(self, message, sender_id, receiver_id, delete_event):
        if "deleted_for" not in message:
            message["deleted_for"]=[]

        if delete_event == "me":
            if sender_id not in message["deleted_for"]:
                message["deleted_for"].append(sender_id)

        elif delete_event =="everyone":
            if sender_id not in message['deleted_for']:
                message["deleted_for"].append(sender_id)
                    
            if receiver_id not in message['deleted_for']:
                message["deleted_for"].append(receiver_id)



    def handle_delete_event_file(self, message, sender_id, receiver_id, delete_event, file_uuids):
        if "file" in message and isinstance(message["file"], list):  
            for file in message["file"]:
                if not isinstance(file, dict):  
                    continue

                if file.get("file_uuid") in file_uuids:
                    file.setdefault("deleted_for", [])

                    if delete_event == "me":
                        if sender_id not in file["deleted_for"]:
                            file["deleted_for"].append(sender_id)

                    elif delete_event == "everyone":
                        if sender_id not in file["deleted_for"]:
                            file["deleted_for"].append(sender_id)

                        if receiver_id and receiver_id not in file["deleted_for"]:
                            file["deleted_for"].append(receiver_id)

        return message 


    def handle_delete_event_forwarded(self, message, sender_id, receiver_id, delete_event, forward_message_ids):
        if "forwarded_content" in message and isinstance(message["forwarded_content"], list):  
            for forwarded_content in message["forwarded_content"]:
                if not isinstance(forwarded_content, dict):  
                    continue

                if forwarded_content.get("message_id") in forward_message_ids:
                    forwarded_content.setdefault("deleted_for", [])

                    if delete_event == "me":
                        if sender_id not in forwarded_content["deleted_for"]:
                            forwarded_content["deleted_for"].append(sender_id)

                    elif delete_event == "everyone":
                        if sender_id not in forwarded_content["deleted_for"]:
                            forwarded_content["deleted_for"].append(sender_id)

                        if receiver_id and receiver_id not in forwarded_content["deleted_for"]:
                            forwarded_content["deleted_for"].append(receiver_id)

        return message 

    def delete(self, request):
        keys = self.load_key()
        # Accept either message_ids or file_uuids as the key
        message_ids = request.data.get("message_ids", [])
        file_uuids = request.data.get("file_uuids", [])
        forward_message_ids=request.data.get("forward_message_ids",[])
        delete_event = request.data.get("delete_event")
        

        try:
            sender_id = request.query_params.get('sender_id')
            receiver_id = request.query_params.get('receiver_id')

            if not sender_id or not receiver_id:
                return Response(
                    {"status": "error", "message": "Both sender_id and receiver_id are required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            chat_message = EmployeeChat.objects.all().order_by('-timestamp')
            deleted_messages = []
            
            for chat in chat_message:              
                filtered_messages = [
                    message for message in sorted(chat.messages, key=lambda m: m["timestamp"], reverse=True)
                    if ((message["sender"] == sender_id and message["receiver"] == receiver_id) or
                        (message["sender"] == receiver_id and message["receiver"] == sender_id)) and
                        "message_id" in message 
                ]
                
                def delete_by_message_ids():
                    messages_to_delete = [
                        msg for msg in filtered_messages 
                        if str(msg.get("message_id")) in [str(mid) for mid in message_ids]
                    ]

                    if messages_to_delete:
                        for message_to_delete in messages_to_delete:
                            self.handle_delete_event(message_to_delete, sender_id, receiver_id, delete_event)

                            json_backup = {
                                "message_id": message_to_delete["message_id"],
                                "sender": message_to_delete["sender"],
                                "receiver": message_to_delete["receiver"],
                                "content": message_to_delete.get("content"),
                                "file": message_to_delete.get("file"),
                                "timestamp": message_to_delete["timestamp"],
                                "deleted_at": timezone.now().isoformat(),    
                                "deleted_for":message_to_delete["deleted_for"],    
                                "format": "json"
                            }
                            string_backup = {
                                "message_id": message_to_delete["message_id"],
                                "content": str(message_to_delete.get("content")),
                                "metadata": f"Deleted by {sender_id} at {timezone.now().isoformat()}",
                                "format": "string"
                            }
                            
                            message_backup.objects.create(
                                key=f"deleted_message_json_{message_to_delete['message_id']}",
                                value=json_backup
                            )
                            deleted_messages.append(message_to_delete)

                        for msg in chat.messages:
                            if msg.get("message_id") in message_ids:
                                msg["deleted"]=True
                                msg["deleted_for"]=message_to_delete["deleted_for"]

                        with transaction.atomic():
                            chat.save(update_fields=['messages'])

                def delete_by_file_uuids():

                    messages_to_update = [
                        msg for msg in filtered_messages 
                        if any(file.get("file_uuid") in file_uuids for file in msg.get("file", []))
                    ]

                    if messages_to_update:
                        for message_to_update in messages_to_update:
                            json_backup = {
                                "message_id": message_to_update["message_id"],
                                "sender": message_to_update["sender"],
                                "receiver": message_to_update["receiver"],
                                "content": message_to_update.get("content"),
                                "file": message_to_update.get("file"),
                                "timestamp": message_to_update["timestamp"],
                                "deleted_at": timezone.now().isoformat(),
                                "format": "json"
                            }

                            string_backup = {
                                "message_id": message_to_update["message_id"],
                                "content": str(message_to_update.get("content")),
                                "metadata": f"Deleted by {sender_id} at {timezone.now().isoformat()}",
                                "format": "string"
                            }
                            
                            message_backup.objects.create(
                                key=f"deleted_message_json_{message_to_update['message_id']}",
                                value=json_backup
                            )


                            for file in message_to_update["file"]:
                                if file.get("file_uuid") in file_uuids:
                                    file["deleted"]=True
                                    self.handle_delete_event_file(message_to_update, sender_id, receiver_id, delete_event, file_uuids)
                            
                            deleted_messages.append({"file": message_to_update["file"]})
                        
                        with transaction.atomic():
                            chat.messages = [
                                msg if msg.get("message_id") != message_to_update["message_id"] else message_to_update
                                for msg in chat.messages
                            ]
                            chat.save(update_fields=['messages'])


                def delete_forward_message():
                    forwarded_message_delete = [
                        msg for msg in filtered_messages 
                        if msg.get("forwarded_content") and isinstance(msg["forwarded_content"], list) and
                        any(forwarded_content.get("message_id") in forward_message_ids
                        for forwarded_content in msg["forwarded_content"])
                    ]
                    

                    if forwarded_message_delete:
                       
                        for message_to_delete in forwarded_message_delete:
                            json_backup = {
                                "message_id": message_to_delete["message_id"],
                                "content": message_to_delete.get("content"),
                                "file": message_to_delete.get("file"),
                                "deleted_at": timezone.now().isoformat(),
                                "format": "json"
                                }
                          
                            string_backup = {
                                "message_id": message_to_delete["message_id"],
                                "content": str(message_to_delete.get("content")),
                                "metadata": f"Deleted by {sender_id} at {timezone.now().isoformat()}",
                                "format": "string"
                                }
                        
                                                 
                            message_backup.objects.create(
                                key=f"deleted_message_json_{message_to_delete['message_id']}",
                                value=json_backup
                                )
        
                            forwarded_content = message_to_delete.get("forwarded_content")
                            if forwarded_content is None:
                                forwarded_content = [] 

                            for forwarded_message in forwarded_content:
                                if forwarded_message.get("message_id") in forward_message_ids:
                                    forwarded_message["deleted"] = True
                                    self.handle_delete_event_forwarded(
                                        message_to_delete, sender_id, receiver_id, delete_event, forward_message_ids
                                    )

                            deleted_messages.append({"forwarded_content": forwarded_content})

                        with transaction.atomic():
                            chat.messages = [
                                msg if msg.get("message_id") != message_to_delete["message_id"] else message_to_delete
                                for msg in chat.messages
                            ]
                            chat.save(update_fields=['messages'])

                if message_ids:
                    delete_by_message_ids()
                if file_uuids:
                    delete_by_file_uuids()

                if forward_message_ids:
                    delete_forward_message()


            if deleted_messages:
                return Response({"status": "Success", "message": f"Successfully deleted", "deleted_messages": deleted_messages}, status=status.HTTP_200_OK)

            return Response({"status": "Error", "message": "No matching messages found to delete"},status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response(
                {"status": "Error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
