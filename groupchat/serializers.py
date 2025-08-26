from rest_framework import serializers
from .models import EmployeeGroup, EmployeeGroupMember, EmployeeGroupChat, MessageStatus
from employee.models import TMEmployeeDetail


# Serializer for employee list based on org to create group
class EmployeeListSerializerGroup(serializers.ModelSerializer):
    class Meta:
        model = TMEmployeeDetail
        fields= ['id', 'ProfileImage','EmployeeName','Status']



class EmployeeGroupSerializersDetails(serializers.ModelSerializer):
    members = EmployeeListSerializerGroup(many=True, read_only=True)
    created_by = EmployeeListSerializerGroup(read_only=True)
    updated_by = EmployeeListSerializerGroup(read_only=True)

    class Meta:
        model = EmployeeGroup
        fields = ['id','groupname','description','members','created_by','created_on','updated_by','updated_on']






class EmployeeGroupMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeGroupMember
        fields = '__all__'

class EmployeeGroupSerializers(serializers.ModelSerializer):
    members = EmployeeGroupMemberSerializer(many=True, write_only=True)

    class Meta:
        model = EmployeeGroup
        fields = '__all__'


    def create(self, validated_data):
        members_data = validated_data.pop('members',[])
        created_by = validated_data['created_by']

        group = EmployeeGroup.objects.create(**validated_data)
        EmployeeGroupMember.objects.create(group=group, user = created_by, is_admin=True)
        for member in members_data:
            user = member['user']
            is_admin = member.get('is_admin',False)
            if user != created_by:
                EmployeeGroupMember.objects.create(group=group, user=user, is_admin=is_admin)
        return group



class EmployeeGroupChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeGroupChat
        fields='__all__'


class MessageStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageStatus
        fields = '__all__'