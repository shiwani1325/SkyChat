from django.db import models

# Create your models here.

class Superadmin(models.Model):
    name = models.CharField(max_length=250)
    email = models.EmailField(max_length=250, null=True)
    password = models.CharField(max_length=100)
    company =models.CharField(max_length=200)
    telephone = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = "Superadmin"

    def __str__(self):
        return self.name



