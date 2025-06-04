from rest_framework import serializers
from .models import Employee
from custom.models import User
from custom.serializers import UserSerializer

class EmployeeSerializers(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    organisation_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Employee
        fields='__all__'

    def create(self, validated_data):
        org_id = validated_data.pop('organisation_id')
        organisation = User.objects.get(id=org_id, role='organisation')
        return Employee.objects.create(organisation=organisation, **validated_data)