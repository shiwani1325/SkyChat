from django.db import models
from org.models import Organisation
from custom.models import User

class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, limit_choices_to={'role': 'employee'}, null=True,blank=True)
    organisation = models.ForeignKey(User, on_delete=models.CASCADE, related_name='employees', limit_choices_to={'role': 'organisation'},null=True,blank=True)
    employee_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    image = models.ImageField(upload_to='images/', null=True, blank=True)
    status = models.CharField(max_length=100, null=True, blank=True)
    mob_number = models.CharField(max_length=20, null=True, blank=True, unique=True)
    department = models.CharField(max_length=100, null=True, blank=True)
    designation = models.CharField(max_length=100, null=True, blank=True)
    date_of_joining = models.DateField(max_length = 20, null=True, blank=True)
    date_of_resign = models.DateField(max_length=20, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=50, null=True, blank=True)
    nationality = models.CharField(max_length=50, null=True, blank=True)
    address = models.CharField(max_length=100, null=True, blank=True)
    father_name = models.CharField(max_length=100, null=True, blank=True)
    mother_name = models.CharField(max_length=100, null=True, blank=True)
    parent_contact = models.CharField(max_length=20, null=True, blank=True)
    employment_type = models.CharField(max_length=100, null=True, blank=True)
    work_location = models.CharField(max_length=100, null=True, blank=True)
    reporting_manager = models.CharField(max_length=100, null=True, blank=True)


    class Meta:
        db_table = 'Employee'


    def __str__(self):
        return f"{self.user.name}-{self.employee_id}"