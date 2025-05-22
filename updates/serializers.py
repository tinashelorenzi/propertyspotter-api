from rest_framework import serializers
from .models import Update
from users.models import CustomUser

class UpdateSerializer(serializers.ModelSerializer):
    recipient = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.filter(role='Spotter'),
        pk_field=serializers.CharField()
    )

    class Meta:
        model = Update
        fields = [
            'id', 'title', 'message', 'update_type', 'recipient',
            'related_lead', 'related_commission', 'delivery_status',
            'whatsapp_message_id', 'delivery_attempts', 'last_attempt_at',
            'created_at', 'updated_at', 'delivered_at', 'read_at'
        ]
        read_only_fields = [
            'delivery_status', 'whatsapp_message_id', 'delivery_attempts',
            'last_attempt_at', 'created_at', 'updated_at', 'delivered_at', 'read_at'
        ] 