from .models import OrgDepartment, OrgDesignation
from rest_framework import serializers


class OrgDepartmentSerializers(serializers.ModelSerializer):
    class Meta:
        model = OrgDepartment
        fields='__all__'



class OrgDesignationSerializers(serializers.ModelSerializer):
    class Meta:
        model = OrgDesignation
        fields = '__all__'