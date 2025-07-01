from django.db import models

# Create your models here.

# class Superadmin(models.Model):
#     user= models.OneToOneField(User, on_delete=models.CASCADE, limit_choices_to={'role':'superadmin'}, null=True, blank=True)
#     company =models.CharField(max_length=200, null=True, blank=True)
#     telephone = models.CharField(max_length=50, unique=True, null=True, blank=True)

#     class Meta:
#         db_table = "Superadmin"

#     def __str__(self):
#         return f"{self.user.name} and {self.company}"


