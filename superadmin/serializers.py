from rest_framework import serializers
from .models import Superadmin

class SuperadminSerializers(serializers.ModelSerializer):
    class Meta:
        model = Superadmin
        fields='__all__'