from rest_framework import serializers
from .models import TMEmployeeDetail
from custom.models import User
from custom.serializers import UserSerializer
from dept.serializers import OrgDepartmentSerializers, OrgDesignationSerializers
from dept.models import OrgDepartment , OrgDesignation

class EmployeeSerializers(serializers.ModelSerializer):
    DepartmentId = serializers.PrimaryKeyRelatedField(queryset=OrgDepartment.objects.all())
    DesignationId = serializers.PrimaryKeyRelatedField(queryset=OrgDesignation.objects.all())

    DeptName = serializers.SerializerMethodField(read_only=True)
    DesName = serializers.SerializerMethodField(read_only=True)
    ProfileImage = serializers.SerializerMethodField()

    class Meta:
        model = TMEmployeeDetail
        exclude = ['CreatedOn', 'UpdatedOn', 'CreatedBy', 'UpdatedBy']

    def get_DeptName(self, obj):
        return obj.DepartmentId.DeptName if obj.DepartmentId else None

    def get_DesName(self, obj):
        return obj.DesignationId.DesName if obj.DesignationId else None

    def get_ProfileImage(self, obj):
        return obj.ProfileImage.url if obj.ProfileImage else None

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep.pop('DepartmentId', None)
        rep.pop('DesignationId', None)
        return rep


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
    class Meta:
        model = TMEmployeeDetail
        exclude = ['CreatedOn', 'UpdatedOn', 'CreatedBy', 'UpdatedBy']


# from rest_framework import serializers
# from .models import TMEmployeeDetail
# from custom.models import User
# from custom.serializers import UserSerializer
# from dept.serializers import OrgDepartmentSerializers, OrgDesignationSerializers
# from dept.models import OrgDepartment , OrgDesignation

# class EmployeeSerializers(serializers.ModelSerializer):
#     DepartmentId = serializers.PrimaryKeyRelatedField(queryset=OrgDepartment.objects.all())
#     DesignationId = serializers.PrimaryKeyRelatedField(queryset=OrgDesignation.objects.all())

#     class Meta:
#         model = TMEmployeeDetail
#         fields = '__all__'

#     def to_representation(self, instance):
#         rep = super().to_representation(instance)
#         rep['DepartmentId'] = OrgDepartmentSerializers(instance.DepartmentId).data
#         rep['DesignationId'] = OrgDesignationSerializers(instance.DesignationId).data
#         return rep


# class UserWithEmployeeSerializer(serializers.ModelSerializer):
    
#     password = serializers.CharField(write_only=True)

#     class Meta:
#         model = User
#         fields = ['email', 'password', 'role', 'admin']


#     def to_internal_value(self, data):
#         self.employee_data = {
#             field: data.pop(field)
#             for field in EmployeeSerializers().get_fields().keys()
#             if field in data
#         }
#         return super().to_internal_value(data)

#     def create(self, validated_data):
#         password = validated_data.pop('password')
#         self.employee_data['CreatedBy'] = self.context['request'].user if self.context.get('request') else None
#         emp_serializer = EmployeeSerializers(data=self.employee_data)
#         emp_serializer.is_valid(raise_exception=True)
#         employee = emp_serializer.save()
#         user = User.objects.create(user=employee, **validated_data)
#         user.set_password(password)
#         user.save()
#         return user