from rest_framework import serializers
from .models import TMOrganisationDetail
from custom.serializers import UserSerializer
from custom.models import User


class OrganisationSerializer(serializers.ModelSerializer):

    class Meta:
        model = TMOrganisationDetail
        exclude = ['CreatedOn', 'UpdatedOn', 'CreatedBy', 'UpdatedBy']




class UserWithOrganisationSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'role']


    def to_internal_value(self, data):
        self.org_data={
            field : data.pop(field)
            for field in OrganisationSerializer().get_fields().keys()
            if field in data
        }
        return super().to_internal_value(data)
    

    def create(self, validated_data):
        password = validated_data.pop('password')
        self.org_data['CreatedBy'] = self.context['request'].user if self.context.get('request') else None
        org_serializer = OrganisationSerializer(data = self.org_data)
        org_serializer.is_valid(raise_exception=True)
        org = org_serializer.save()
        user = User.objects.create(org_id=org, **validated_data)
        user.set_password(password)
        user.save()
        return user