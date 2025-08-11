from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import TMRole

@receiver(post_migrate)
def create_default_roles(sender, **kwargs):
    roles = [
        ('1','Superadmin'),
        ('2', 'Admin'),
        ('3','User'),
    ]

    for role_id, role_name in roles:
        TMRole.objects.get_or_create(id= role_id, RoleName=role_name)