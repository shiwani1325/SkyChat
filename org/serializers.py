from rest_framework import serializers
from .models import Organisation

class OrganisationSerializers(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields='__all__'