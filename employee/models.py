from django.db import models
from org.models import Organisation

class Employee(models.Model):
    Org_id = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='images/', null=True, blank=True)
    email = models.CharField(max_length=200, unique=True, null=True, blank=True)
    status = models.CharField(max_length=100, null=True, blank=True)
    mob_number = models.CharField(max_length=20, null=True, blank=True, unique=True)
    password = models.CharField(max_length=50)
    Department = models.CharField(max_length=100, null=True, blank=True)
    Designation = models.CharField(max_length=100, null=True, blank=True)
    Date_of_joning = models.DateField(max_length = 20, null=True, blank=True)
    Date_of_resign = models.DateField(max_length=20, null=True, blank=True)
    Dateofbirth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=50, null=True, blank=True)
    Nationality = models.CharField(max_length=50, null=True, blank=True)
    Address = models.CharField(max_length=100, null=True, blank=True)
    Father_name = models.CharField(max_length=100, null=True, blank=True)
    Mother_name = models.CharField(max_length=100, null=True, blank=True)
    parentcontact = models.CharField(max_length=20, null=True, blank=True)
    EmploymentType = models.CharField(max_length=100, null=True, blank=True)
    WorkLocation = models.CharField(max_length=100, null=True, blank=True)
    ReportingManager = models.CharField(max_length=100, null=True, blank=True)


    class Meta:
        db_table = 'Employee'


    def __str__(self):
        return f"{self.name}-{self.employee_id}"
