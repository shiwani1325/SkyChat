from rest_framework import serializers
from .models import EmployeeChat, ERp_backup

class EmployeeChatSerializer(serializers.ModelSerializer):
    sender = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    receiver = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    model = EmployeeChat
    fields = '__all__'


class ERp_backupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ERp_backup
        fields = '__all__'