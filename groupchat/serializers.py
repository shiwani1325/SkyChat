from rest_framework import serializers
from .models import EmployeeGroup, EmployeeGroupMember,EmployeeGroupChat
from employee.models import TMEmployeeDetail


# Serializer to display employee list
class EmployeeListSerializerGroup(serializers.ModelSerializer):
    class Meta:
        model = TMEmployeeDetail
        fields = ['id','EmployeeName','ProfileImage','Status']


# Group member serializer (for create purpose)
class EmployeeGroupMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeGroupMember
        fields = ['id', 'user', 'is_admin']


# Group serializer with members
class EmployeeGroupSerializer(serializers.ModelSerializer):
    members = EmployeeGroupMemberSerializer(many=True, write_only=True)

    class Meta:
        model = EmployeeGroup
        fields = ['id', 'groupname', 'description', 'created_by', 'members']

    def create(self, validated_data):
        members_data = validated_data.pop("members", [])
        group = EmployeeGroup.objects.create(**validated_data)

        # Add members
        for member in members_data:
            EmployeeGroupMember.objects.create(
                group=group,
                user=member.get("user"),
                is_admin=member.get("is_admin", False)
            )
        return group



class EmployeeGroupChatSerializer(serializers.ModelSerializer):
    group = serializers.PrimaryKeyRelatedField(read_only=True)
    sender = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = EmployeeGroupChat
        fields = '__all__'