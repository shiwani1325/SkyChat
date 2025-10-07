from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from employee.models import TMEmployeeDetail
from org.models import TMOrganisationDetail
from django.utils import timezone



class TMRole(models.Model):
    ROLE_CHOICES = [
        ('1','Superadmin'),
        ('2', 'Admin'),
        ('3','User'),
    ]

    id = models.PositiveSmallIntegerField(primary_key=True, choices=ROLE_CHOICES)
    RoleName = models.CharField(max_length=20, unique=True)

    class Meta:
        db_table = 'TMRole'

    def __str__(self):
        return self.RoleName


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email).lower()

        emp =extra_fields.get('emp_id', None)
        org= extra_fields.get('org_id', None)
        if not password:
            name_part = "User"
            mob_part = "0000"

            if emp:
                name_part = (emp.EmployeeName[:4] if emp.EmployeeName else 'User').lower()
                mob_part = (emp.EmpMobNumber[-4:] if emp.EmpMobNumber else '0000')
            elif org:
                name_part = (org.OrgName[:4] if org.OrgName else 'Org')
                mob_part = (org.ContPerNum[-4:] if org.ContPerNum else '0000')
            

            password = name_part + mob_part
        # extra_fields['raw_password'] = password
        # raw_password = password

        # Ensure raw_password is NOT passed to User model
        # extra_fields.pop('raw_password', None)


        user = self.model(email=email, **extra_fields)
        user.set_password(password) 
        user.raw_password = password
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        try:
            superadmin_role = TMRole.objects.get(RoleName='Superadmin')
        except TMRole.DoesNotExist:
            superadmin_role = TMRole.objects.create(RoleName='Superadmin')

        extra_fields.setdefault('role', superadmin_role)
        extra_fields.setdefault('name', "Shiwani")
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.CharField(unique=True)
    role = models.ForeignKey(TMRole, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=100, null=True, blank=True)  
    org_id = models.ForeignKey(TMOrganisationDetail, on_delete=models.SET_NULL, null=True, blank=True)
    emp_id = models.ForeignKey(TMEmployeeDetail, on_delete=models.SET_NULL, null=True, blank=True)
    raw_password = models.CharField(max_length=128, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created_on = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [ ]

    objects = UserManager()

    class Meta:
        db_table = 'User'
    

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.lower()
        super().save(*args, **kwargs)