from rest_framework import serializers
from .models import Organisation
from custom.serializers import UserSerializer

class OrganisationSerializers(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Organisation
        fields='__all__'