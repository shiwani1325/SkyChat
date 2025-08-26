from django.db import models
from django.conf import settings
from employee.models import TMEmployeeDetail
from django.utils import timezone


User = settings.AUTH_USER_MODEL

class EmployeeGroup(models.Model):
    groupname = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_groups")
    created_on = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_on = models.DateTimeField(auto_now=True, null=True, blank=True)

class EmployeeGroupMember(models.Model):
    group = models.ForeignKey(EmployeeGroup, on_delete=models.CASCADE, related_name="memberships", null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    joined_at = models.DateTimeField(default=timezone.now, null=True, blank=True)
    is_admin = models.BooleanField(default=False, null=True, blank=True)

class EmployeeGroupChat(models.Model):
    group = models.ForeignKey(EmployeeGroup, on_delete=models.CASCADE, related_name="messages", null=True, blank=True)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    message_type = models.CharField(max_length=20, choices=[
        ('text','text'),
        ('image','image'),
        ('video','video'),
        ('audio','audio'),
        ('file','file'),
    ], default='text', null=True, blank=True)
    content = models.TextField(blank=True, null=True)
    file_url = models.URLField(blank=True, null=True)  # or FileField if you manage uploads
    timestamp = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [models.Index(fields=['group','timestamp'])]

class MessageStatus(models.Model):
    message = models.ForeignKey(EmployeeGroupChat, on_delete=models.CASCADE, related_name="statuses")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    delivered = models.BooleanField(default=False)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("message", "user")
