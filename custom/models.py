from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from employee.models import TMEmployeeDetail
from org.models import TMOrganisationDetail
from django.utils import timezone



class TMRole(models.Model):
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
        user = self.model(email=email, **extra_fields)
        user.set_password(password) 
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
    email = models.EmailField(unique=True)
    role = models.ForeignKey(TMRole, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=100, null=True, blank=True)  
    org_id = models.ForeignKey(TMOrganisationDetail, on_delete=models.SET_NULL, null=True, blank=True)
    emp_id = models.ForeignKey(TMEmployeeDetail, on_delete=models.SET_NULL, null=True, blank=True)

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