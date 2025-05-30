from rest_framework import serializers
from .models import Employee

class EmployeeSerializers(serializers.ModelSerializer):
    Org_id = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Employee
        #exclude = ['password'] 
        fields='__all__'