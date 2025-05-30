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
    property_details = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()
    
    class Meta:
        model = Lead
        fields = [
            'id', 'first_name', 'last_name', 'email', 'phone',
            'status', 'is_accepted', 'notes_text', 'images', 'spotter', 'agent', 
            'requested_agent', 'assigned_agency', 'property_details', 'notes',
            'agreed_commission_amount', 'spotter_commission_amount',
            'created_at', 'updated_at', 'assigned_at', 'accepted_at', 'closed_at'
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

    def get_property_details(self, obj):
        if obj.property:
            return {
                'id': obj.property.id,
                'title': obj.property.title,
                'description': obj.property.description,
                'property_type': obj.property.property_type,
                'status': obj.property.status,
                'price': obj.property.price,
                'address': obj.property.address,
                'city': obj.property.city,
                'state': obj.property.state,
                'zip_code': obj.property.zip_code,
                'bedrooms': obj.property.bedrooms,
                'bathrooms': obj.property.bathrooms,
                'square_feet': obj.property.square_feet,
                'lot_size': obj.property.lot_size,
                'year_built': obj.property.year_built,
                'listing_url': obj.property.listing_url,
                'created_at': obj.property.created_at,
                'updated_at': obj.property.updated_at
            }
        return None

    def get_notes(self, obj):
        return [{
            'id': note.id,
            'content': note.content,
            'created_by': {
                'id': note.created_by.id,
                'email': note.created_by.email,
                'role': note.created_by.role
            },
            'created_at': note.created_at
        } for note in obj.notes.all().order_by('-created_at')]

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
            'id', 'first_name', 'last_name', 'email', 'phone', 'street_address', 'suburb',
            'status', 'is_accepted', 'notes_text', 'images', 'spotter', 'agent', 'requested_agent',
            'agreed_commission_amount', 'spotter_commission_amount',
            'created_at', 'updated_at', 'assigned_at', 'accepted_at', 'closed_at',
            'property_details'
        ]
    
    def get_property_details(self, obj):
        if obj.property:
            return {
                'id': obj.property.id,
                'title': obj.property.title,
                'address': obj.property.address,
                'price': obj.property.price,
                'status': obj.property.status,
                'listing_url': obj.property.listing_url
            }
        return None

class AgentLeadsSerializer(serializers.ModelSerializer):
    images = LeadImageSerializer(many=True, read_only=True)
    spotter = UserDetailSerializer(read_only=True)
    agent = UserDetailSerializer(read_only=True)
    requested_agent = UserDetailSerializer(read_only=True)
    property_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Lead
        fields = [
            'id', 'first_name', 'last_name', 'email', 'phone', 'street_address', 'suburb',
            'status', 'is_accepted', 'notes_text', 'images', 'spotter', 'agent', 'requested_agent',
            'agreed_commission_amount', 'spotter_commission_amount',
            'created_at', 'updated_at', 'assigned_at', 'accepted_at', 'closed_at',
            'property_details'
        ]
    
    def get_property_details(self, obj):
        if obj.property:
            return {
                'id': obj.property.id,
                'title': obj.property.title,
                'address': obj.property.address,
                'price': obj.property.price,
                'status': obj.property.status,
                'listing_url': obj.property.listing_url
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

class LeadAcceptanceSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['accept', 'reject'], required=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        lead = self.context.get('lead')
        if not lead:
            raise serializers.ValidationError("Lead not found")
        
        if lead.status == 'closed':
            raise serializers.ValidationError("Cannot accept or reject a closed lead")
            
        if data['action'] == 'accept' and lead.is_accepted:
            raise serializers.ValidationError("Lead is already accepted")
            
        if data['action'] == 'reject' and not lead.is_accepted:
            raise serializers.ValidationError("Lead is already rejected")
            
        return data

class LeadPropertyUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating property details of a lead
    """
    # Property Details
    title = serializers.CharField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_null=True)
    property_type = serializers.ChoiceField(choices=['residential', 'commercial', 'land'], required=False, allow_null=True)
    status = serializers.ChoiceField(choices=['available', 'pending', 'sold'], required=False, allow_null=True)
    price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    address = serializers.CharField(required=False, allow_null=True)
    city = serializers.CharField(required=False, allow_null=True)
    state = serializers.CharField(required=False, allow_null=True)
    zip_code = serializers.CharField(required=False, allow_null=True)
    bedrooms = serializers.IntegerField(required=False, allow_null=True)
    bathrooms = serializers.DecimalField(max_digits=3, decimal_places=1, required=False, allow_null=True)
    square_feet = serializers.IntegerField(required=False, allow_null=True)
    lot_size = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    year_built = serializers.IntegerField(required=False, allow_null=True)
    listing_url = serializers.URLField(required=False, allow_null=True)
    
    # Commission Information
    agreed_commission_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_null=True)

    def validate(self, data):
        lead = self.context.get('lead')
        if not lead:
            raise serializers.ValidationError("Lead not found")
            
        if not lead.property:
            raise serializers.ValidationError("Lead has no associated property")
            
        if lead.status == 'closed':
            raise serializers.ValidationError("Cannot update a closed lead's property")
            
        return data

    def update(self, instance, validated_data):
        lead = self.context.get('lead')
        property = lead.property
        
        # Update property fields
        for field, value in validated_data.items():
            if field in ['agreed_commission_amount', 'notes']:
                continue
            if hasattr(property, field):
                setattr(property, field, value)
        
        # Update lead fields
        if 'agreed_commission_amount' in validated_data:
            lead.agreed_commission_amount = validated_data['agreed_commission_amount']
            lead.calculate_commissions()  # This will calculate spotter commission and platform fee
            
        if 'notes' in validated_data:
            lead.notes_text = validated_data['notes']
        
        property.save()
        lead.save()
        
        return lead

class LeadWhatsAppNotificationSerializer(serializers.Serializer):
    """
    Serializer for sending WhatsApp notifications about lead updates
    """
    template_name = serializers.CharField(required=True)
    variables = serializers.DictField(
        child=serializers.CharField(),
        required=True
    )

    def validate_template_name(self, value):
        from updates.twilio_handler import MESSAGE_TEMPLATES
        if value not in MESSAGE_TEMPLATES:
            raise serializers.ValidationError(f"Invalid template name. Available templates: {list(MESSAGE_TEMPLATES.keys())}")
        return value

    def validate(self, data):
        from updates.twilio_handler import MESSAGE_TEMPLATES
        template = MESSAGE_TEMPLATES[data['template_name']]
        required_vars = set()
        
        # Extract required variables from template
        import re
        matches = re.findall(r'{{(\d+)}}', template)
        required_vars = set(matches)
        
        # Check if all required variables are provided
        provided_vars = set(data['variables'].keys())
        missing_vars = required_vars - provided_vars
        
        if missing_vars:
            raise serializers.ValidationError(
                f"Missing required variables for template: {missing_vars}"
            )
            
        return data

class LeadCompletionSerializer(serializers.Serializer):
    """
    Serializer for marking a lead as complete (property sold)
    """
    final_price = serializers.DecimalField(max_digits=12, decimal_places=2, required=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        lead = self.context.get('lead')
        if not lead:
            raise serializers.ValidationError("Lead not found")
            
        if not lead.property:
            raise serializers.ValidationError("Lead has no associated property")
            
        if lead.status == 'closed':
            raise serializers.ValidationError("Lead is already closed")
            
        return data

class LeadFailureSerializer(serializers.Serializer):
    """
    Serializer for marking a lead as failed
    """
    reason = serializers.CharField(required=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        lead = self.context.get('lead')
        if not lead:
            raise serializers.ValidationError("Lead not found")
            
        if lead.status == 'closed':
            raise serializers.ValidationError("Lead is already closed")
            
        return data