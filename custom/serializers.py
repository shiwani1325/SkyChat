from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import User, TMRole

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_null=True,
        allow_blank=True
    )
    role_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'role', 'role_name', 'password', 'org_id', 'emp_id', 'name']
        extra_kwargs = {'password': {'write_only': True}}

    # def get_role_name(self,obj):
    #     if obj.role:
    #         return obj.role.RoleName
    #     return None

    def get_role_name(self, obj):
        role = getattr(obj, 'role', None)
        if role:
            return getattr(role, 'RoleName', None)
        return None




    # edited on #18-07-2025
    # def get_name(self, obj):
    #     if obj.role and obj.role.RoleName == "Superadmin":
    #         return obj.name
    #     return None

    def validate(self, data):

        role = data.get('role') or (self.instance.role if self.instance else None)
        name = data.get('name')

        if role and role.RoleName != "Superadmin" and name:
            raise serializers.ValidationError("Only Superadmin can have a name.")
        return data

    def create(self, validated_data):
        password = validated_data.pop('password', None)

        # This handles: password is None, '', or just blank
        if password:
            return User.objects.create_user(password=password, **validated_data)

        # No password provided – let manager auto-generate it
        return User.objects.create_user(**validated_data)


class RoleSerializers(serializers.ModelSerializer):
    class Meta:
        model = TMRole
        fields = '__all__'