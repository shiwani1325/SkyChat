from django.db import models
from employee.models import TMEmployeeDetail
from datetime import datetime
import pytz
from cryptography.fernet import Fernet
import uuid

class EmployeeChat(models.Model):

    STATUS_CHOICES=[
        ("sent","Sent"),
        ("delivered","Delivered"),
        ("seen","Seen")]

    sender=models.ForeignKey(TMEmployeeDetail, related_name="sender_message", on_delete=models.CASCADE)
    receiver=models.ForeignKey(TMEmployeeDetail,related_name="receiver_message", on_delete=models.CASCADE)
    messages=models.JSONField(default=list, null=True, blank=True)
    timestamp=models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table="EmployeeChat"
        unique_together=('sender','receiver')

    def add_message(self, sender_id, receiver_id,sender_name=None, receiver_name=None, content=None, file=None, read=False, message_id=None, status=None, message_type=None, replied_to=None, forwarded_content=None ):
        ist_timezone = pytz.timezone("Asia/Kolkata")
        ist_timestamp = datetime.now().astimezone(ist_timezone).isoformat()
        # message_id = str(uuid.uuid4())
        new_message = {
            "message_id":message_id,
            "sender": sender_id,
            "receiver": receiver_id,
            "sender_name":sender_name,
            "receiver_name":receiver_name,
            "timestamp": ist_timestamp,
            "read": read,
            "status":status,
            "content": None,
            "message_type":message_type,
            "replied_to":replied_to,
            "forwarded_content":forwarded_content
        }
        if content and content.strip():
            new_message["content"] = content
        if file is not None:
            new_message["file"] = file
        # if file_name is not None:
        #     new_message["file_name"]=file_name
        self.messages.append(new_message)
        self.save()
        return message_id

    def update_message_status(self, message_id, new_status):
        valid_statuses = dict(self.STATUS_CHOICES).keys()
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status: {new_status}. Must be one of {valid_statuses}")


        for message in self.messages:
            if message['message_id'] == message_id:
                message['status'] = new_status
                self.save()
                return True
            
        return False


    def __str__(self):
        return f'Message in {self.sender} - {self.receiver}'


# class ERp_backup(models.Model):
#     key = models.CharField(max_length=255)
#     value = models.JSONField()
#     created_at = models.DateTimeField(auto_now_add=True)
#     read_at = models.DateTimeField(null=True, blank=True)
#     deleted_at = models.DateTimeField(null=True, blank=True)

#     class Meta:
#         db_table = 'erp_backup'  

#     def __str__(self):
#         return self.key




class message_backup(models.Model):
    key = models.CharField(max_length=255)
    value = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'message_backup'  

    def __str__(self):
        return self.key