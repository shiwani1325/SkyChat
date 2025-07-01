from rest_framework import serializers
from .models import TMOrganisationDetail
from custom.serializers import UserSerializer
from custom.models import User


class OrganisationSerializer(serializers.ModelSerializer):
    UserEmail  = serializers.SerializerMethodField()

    class Meta:
        model = TMOrganisationDetail
        exclude = ['CreatedOn', 'UpdatedOn', 'CreatedBy', 'UpdatedBy']
        
    def get_UserEmail(self, obj):
        user = User.objects.filter(org_id=obj).first()
        return user.email if user else None




class UserWithOrganisationSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'role']


    def to_internal_value(self, data):
        clean_data={}
        for key,value in data.items():
            if isinstance(value, list) and len(value)==1:
                clean_data[key] = value[0]
            else:
                clean_data[key]=value

        self.org_data={
            field : clean_data.pop(field)
            for field in OrganisationSerializer().get_fields().keys()
            if field in clean_data
        }
        return super().to_internal_value(clean_data)
    

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