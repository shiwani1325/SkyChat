from django.contrib import admin
from .models import EmployeeGroup, EmployeeGroupMember, EmployeeGroupChat, MessageStatus
# Register your models here.

admin.site.register(EmployeeGroup)
admin.site.register(EmployeeGroupMember)
admin.site.register(EmployeeGroupChat)
admin.site.register(MessageStatus)

