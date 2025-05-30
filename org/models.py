from django.db import models

# Create your models here.


class Organisation(models.Model):
    OrgCode = models.CharField(max_length=100, null=True, blank=True)
    OrgName = models.CharField(max_length=150, null=True, blank=True)
    OrgEmail = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)
    OrgNumber = models.CharField(max_length=20, unique=True)


    class Meta:
        db_table = "Organisation"

    def __str__(self):
        return self.OrgName