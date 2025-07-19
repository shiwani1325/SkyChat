import os
import uuid
from django.db import models
from dept.models import OrgDepartment, OrgDesignation
from django.conf import settings
from django.utils import timezone


def profile_image_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('employee_profiles/', filename)

class TMEmployeeDetail(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]

    EmployeeName = models.CharField(max_length=255)
    EmployeeId = models.CharField(max_length=50, unique=True)  
    EmpMobNumber = models.CharField(max_length=20, unique=True)
    DepartmentId = models.ForeignKey(OrgDepartment, on_delete=models.SET_NULL, null=True)
    DesignationId = models.ForeignKey(OrgDesignation, on_delete=models.SET_NULL, null=True)
    ProfileImage = models.ImageField(upload_to=profile_image_upload_path, null=True, blank=True)
    DateOfJoining = models.DateField()
    Status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    DateOfBirth = models.DateField()
    Gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    Address = models.TextField()
    WorkLocation = models.CharField(max_length=255)
    CreatedOn = models.DateTimeField(auto_now_add=True)
    CreatedBy = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='emp_created')
    UpdatedOn = models.DateTimeField(auto_now=True)
    UpdatedBy = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='emp_updated')

    class Meta:
        db_table = 'TMEmployeeDetail'

    def __str__(self):
        return f"{self.EmployeeName} ({self.EmployeeId})"

    