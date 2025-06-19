from django.db import models
from django.conf import settings
from django.utils import timezone


def logo_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('organisation_logos/', filename)

class TMOrganisationDetail(models.Model):

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    OrgName = models.CharField(max_length=100)
    OrgCode = models.CharField(max_length=100)
    OrgMobNum = models.CharField(max_length=20, unique=True)
    Address = models.TextField()
    ContPer = models.CharField(max_length=100)
    ContPerEmail = models.EmailField()
    ContPerNum = models.CharField(max_length=20, unique=True)
    LogoImg = models.ImageField(upload_to=logo_upload_path, null=True, blank=True)
    BusinessType = models.CharField(max_length=100)
    RegistrationNumber = models.CharField(max_length=100, unique=True)
    CreatedOn = models.DateTimeField(auto_now_add=True)
    CreatedBy = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='org_created')
    UpdatedOn = models.DateTimeField(auto_now=True)
    UpdatedBy = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='org_updated')
    Status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    class Meta:
        db_table = 'TMOrganisationDetail'

    def __str__(self):
        return self.OrgName