from rest_framework import serializers
from .models import Superadmin
from custom.serializers import UserSerializer

class SuperadminSerializers(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Superadmin
        fields='__all__'
        extra_kwargs = {
            'user': {'read_only': True}
        }