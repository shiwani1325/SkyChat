from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, role=None, **extra_fields):
        if not email:
            raise ValueError("User must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password = None, **extra_fields):
        extra_fields.setdefault('role','superadmin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('superadmin', 'SuperAdmin'),
        ('organisation','Organisation'),
        ('employee','Employee')
    ]

    email = models.EmailField(unique = True, null=True, blank=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    role = models.CharField(max_length=20, choices = ROLE_CHOICES, null=True, blank=True)
    is_active = models.BooleanField(default=True, null=True, blank=True)
    is_staff = models.BooleanField(default=False, null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD='email'
    REQUIRED_FIELDS = ['role']

    def __str__(self):
        return f"{self.role.upper()}-{self.email}"

