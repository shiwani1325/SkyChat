from rest_framework import serializers
from .models import TMEmployeeDetail
from custom.models import User
from custom.serializers import UserSerializer
from dept.serializers import OrgDepartmentSerializers, OrgDesignationSerializers
from dept.models import OrgDepartment , OrgDesignation

class EmployeeSerializers(serializers.ModelSerializer):
    DeptName = serializers.CharField(source='DepartmentId.DeptName', read_only=True)
    DesName = serializers.CharField(source='DesignationId.DesName', read_only=True)
    ProfileImage = serializers.SerializerMethodField()
    UserEmail = serializers.SerializerMethodField()

    class Meta:
        model = TMEmployeeDetail
        exclude = ['CreatedOn', 'UpdatedOn', 'CreatedBy', 'UpdatedBy', 'DepartmentId', 'DesignationId']

    def get_ProfileImage(self, obj):
        return obj.ProfileImage.url if obj.ProfileImage else None

    def get_UserEmail(self, obj):
        user = User.objects.filter(emp_id=obj).first()
        return user.email if user else None


class UserWithEmployeeSerializer(serializers.ModelSerializer):
    
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'role', 'org_id']


    def to_internal_value(self, data):
        self.employee_data = {
            field: data.pop(field)
            for field in EmployeeSerializers().get_fields().keys()
            if field in data
        }
        return super().to_internal_value(data)

    def create(self, validated_data):
        password = validated_data.pop('password')
        self.employee_data['CreatedBy'] = self.context['request'].user if self.context.get('request') else None
        emp_serializer = EmployeeSerializers(data=self.employee_data)
        emp_serializer.is_valid(raise_exception=True)
        employee = emp_serializer.save()
        user = User.objects.create(emp_id=employee, **validated_data)
        user.set_password(password)
        user.save()
        return user



class EditEmployeeSerializers(serializers.ModelSerializer):
    UserEmail = serializers.SerializerMethodField()
    class Meta:
        model = TMEmployeeDetail
        exclude = ['CreatedOn', 'UpdatedOn', 'CreatedBy', 'UpdatedBy']
    
    def get_UserEmail(self, obj):
        user = User.objects.filter(emp_id=obj).first()
        return user.email if user else None

