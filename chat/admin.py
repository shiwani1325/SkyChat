from django.contrib import admin
from .models import EmployeeChat, message_backup

admin.site.register(EmployeeChat)
admin.site.register(message_backup)