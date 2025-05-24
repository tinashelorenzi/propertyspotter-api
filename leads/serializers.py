from rest_framework import serializers
from .models import Lead, LeadImage
from users.serializers import UserDetailSerializer
from users.models import CustomUser

class LeadImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadImage
        fields = ['image', 'description']

class LeadListSerializer(serializers.ModelSerializer):
    images = LeadImageSerializer(many=True, read_only=True)
    spotter = UserDetailSerializer(read_only=True)
    agent = UserDetailSerializer(read_only=True)
    requested_agent = UserDetailSerializer(read_only=True)
    
    class Meta:
        model = Lead
        fields = [
            'id', 'first_name', 'last_name', 'email', 'phone',
            'status', 'notes_text', 'images', 'spotter', 'agent', 'requested_agent',
            'agreed_commission_amount', 'spotter_commission_amount',
            'created_at', 'updated_at', 'assigned_at', 'closed_at'
        ]
        read_only_fields = [
            'status', 'agent', 'agreed_commission_amount',
            'spotter_commission_amount', 'assigned_at', 'closed_at'
        ]

class AgencyLeadsSerializer(serializers.ModelSerializer):
    images = LeadImageSerializer(many=True, read_only=True)
    spotter = UserDetailSerializer(read_only=True)
    agent = UserDetailSerializer(read_only=True)
    requested_agent = UserDetailSerializer(read_only=True)
    property_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Lead
        fields = [
            'id', 'first_name', 'last_name', 'email', 'phone',
            'status', 'notes_text', 'images', 'spotter', 'agent', 'requested_agent',
            'agreed_commission_amount', 'spotter_commission_amount',
            'created_at', 'updated_at', 'assigned_at', 'closed_at',
            'property_details'
        ]
    
    def get_property_details(self, obj):
        if obj.property:
            return {
                'id': obj.property.id,
                'title': obj.property.title,
                'address': obj.property.address,
                'price': obj.property.price,
                'status': obj.property.status
            }
        return None

class LeadSubmissionSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for lead submission.
    The actual lead creation logic is handled in the view.
    """
    class Meta:
        model = Lead
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'notes_text'
        ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
            'phone': {'required': True},
            'notes_text': {'required': False}
        }