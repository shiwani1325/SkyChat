from django.db import models
from django.conf import settings
from employee.models import TMEmployeeDetail


class EmployeeGroup(models.Model):
    groupname = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    # members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='empgroup')
    members = models.ManyToManyField(TMEmployeeDetail, null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    # created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='group_created_by')
    created_by = models.ForeignKey(TMEmployeeDetail, on_delete=models.SET_NULL, null=True, blank=True, related_name='group_created_on')
    updated_on = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    # updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='group_updated_by')
    updated_by = models.ForeignKey(TMEmployeeDetail, on_delete=models.SET_NULL, null= True, blank=True, related_name='group_created_by')

    class Meta:
        db_table = 'EmployeeGroup'

    def __str__(self):
        return self.groupname

class EmployeeGroupChat(models.Model):
    group = models.ForeignKey(EmployeeGroup, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message_type = models.CharField(max_length=20, choices=[
        ('text','text'),
        ('image','image'),
        ('video','video'),
        ('audio','audio'),
        ('file','file'),
    ],
    default='text',
    )
    content = models.TextField(blank=True, null=True)
    file_url=models.URLField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields = ['group','timestamp']),
        ]

    def __str__(self):
        return f"{self.sender} in {self.group} at {self.timestamp}"



