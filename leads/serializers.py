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

class LeadSubmissionSerializer(serializers.ModelSerializer):
    images = LeadImageSerializer(many=True, required=False)
    requested_agent = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.filter(role='Agent'),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Lead
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'notes_text', 'images', 'requested_agent'
        ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
            'phone': {'required': True},
            'notes_text': {'required': False},
            'images': {'required': False},
            'requested_agent': {'required': False}
        }

    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        
        # Set the spotter to the current user
        validated_data['spotter'] = self.context['request'].user
        
        # Create the lead
        lead = Lead.objects.create(**validated_data)
        
        # Create associated images if any
        for image_data in images_data:
            LeadImage.objects.create(lead=lead, **image_data)
        
        return lead 