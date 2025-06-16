from rest_framework import serializers
from .models import ContactEntry

class ContactEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactEntry
        fields = ['name', 'email', 'message']
        read_only_fields = ['created_at', 'is_read'] 