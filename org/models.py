from django.db import models
from custom.models import User
# Create your models here.


class Organisation(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, limit_choices_to={'role': 'organisation'},null=True,blank=True)
    OrgCode = models.CharField(max_length=100, null=True, blank=True)
    OrgNumber = models.CharField(max_length=20, unique=True, null=True, blank=True)


    class Meta:
        db_table = "Organisation"

    def __str__(self):
        return f"{self.user.name} and {self.OrgCode}"