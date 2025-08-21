from rest_framework import serializers
from .models import EmployeeGroup
from employee.models import TMEmployeeDetail

class EmployeeGroupSerializers(serializers.ModelSerializer):
    class Meta:
        model = EmployeeGroup
        fields = '__all__'


class EmployeeSerializerGroup(serializers.ModelSerializer):
    class Meta:
        model = TMEmployeeDetail
        fields= ['id', 'ProfileImage','EmployeeName','Status']


class EmployeeGroupSerializersDetails(serializers.ModelSerializer):
    members = EmployeeSerializerGroup(many=True, read_only=True)
    created_by = EmployeeSerializerGroup(read_only=True)
    updated_by = EmployeeSerializerGroup(read_only=True)

    class Meta:
        model = EmployeeGroup
        fields = ['id','groupname','description','members','created_by','created_on','updated_by','updated_on']


