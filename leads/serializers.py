from rest_framework import serializers
from .models import Lead, LeadImage
from users.serializers import UserDetailSerializer
from users.models import CustomUser

class LeadImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadImage
        fields = ['image', 'description']

class LeadDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed lead information
    """
    images = LeadImageSerializer(many=True, read_only=True)
    spotter = UserDetailSerializer(read_only=True)
    agent = UserDetailSerializer(read_only=True)
    requested_agent = UserDetailSerializer(read_only=True)
    assigned_agency = serializers.SerializerMethodField()
    
    class Meta:
        model = Lead
        fields = [
            'id', 'first_name', 'last_name', 'email', 'phone',
            'status', 'notes_text', 'images', 'spotter', 'agent', 
            'requested_agent', 'assigned_agency',
            'agreed_commission_amount', 'spotter_commission_amount',
            'created_at', 'updated_at', 'assigned_at', 'closed_at'
        ]
        read_only_fields = fields

    def get_assigned_agency(self, obj):
        if obj.assigned_agency:
            return {
                'id': obj.assigned_agency.id,
                'name': obj.assigned_agency.name,
                'email': obj.assigned_agency.email,
                'phone': obj.assigned_agency.phone,
                'address': obj.assigned_agency.address
            }
        return None

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

class LeadAssignmentSerializer(serializers.Serializer):
    agent_id = serializers.UUIDField(required=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_agent_id(self, value):
        try:
            agent = CustomUser.objects.get(id=value, role__in=['Agent', 'Agency_Admin'])
            return value
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("Agent not found or is not an agent/agency admin")

    def validate(self, data):
        # Get the lead instance from the context
        lead = self.context.get('lead')
        agent = CustomUser.objects.get(id=data['agent_id'])

        # Check if agent belongs to the same agency as the lead
        if agent.agency_id != lead.assigned_agency_id:
            raise serializers.ValidationError("Agent must belong to the same agency as the lead")

        return data

    def update(self, instance, validated_data):
        agent = CustomUser.objects.get(id=validated_data['agent_id'])
        instance.assigned_agent = agent
        if validated_data.get('notes'):
            instance.notes_text = validated_data['notes']
        instance.save()
        return instance