from rest_framework import serializers
from .models import PropertyListing, PropertyImage

class PropertyImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = PropertyImage
        fields = ['id', 'image', 'image_url', 'alt_text', 'is_primary', 'order']
        read_only_fields = ['id', 'image_url']
    
    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            url = obj.image.url
            if request is not None:
                return request.build_absolute_uri(url)
            return url
        return None

class PropertyListingListSerializer(serializers.ModelSerializer):
    """Serializer for listing properties (summary view)"""
    primary_image_url = serializers.SerializerMethodField()
    agent_name = serializers.CharField(source='agent.get_full_name', read_only=True)
    display_property_type = serializers.CharField(read_only=True)
    
    class Meta:
        model = PropertyListing
        fields = [
            'id', 'title', 'suburb', 'province', 'street_address',
            'property_type', 'display_property_type', 'bedrooms', 'bathrooms',
            'parking_spaces', 'listing_price', 'is_pet_friendly', 'has_pool',
            'is_featured', 'primary_image_url', 'agent_name', 'published_at',
            'view_count'
        ]
        read_only_fields = ['id', 'primary_image_url', 'agent_name', 'published_at', 'view_count']
    
    def get_primary_image_url(self, obj):
        primary_image = obj.primary_image
        if primary_image:
            request = self.context.get('request')
            if primary_image.image and hasattr(primary_image.image, 'url'):
                url = primary_image.image.url
                if request is not None:
                    return request.build_absolute_uri(url)
                return url
        return None

class PropertyListingDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed property view"""
    images = PropertyImageSerializer(many=True, read_only=True)
    agent_name = serializers.CharField(source='agent.get_full_name', read_only=True)
    agent_email = serializers.CharField(source='agent.email', read_only=True)
    agent_phone = serializers.CharField(source='agent.phone', read_only=True)
    display_property_type = serializers.CharField(read_only=True)
    
    class Meta:
        model = PropertyListing
        fields = [
            'id', 'title', 'description', 'suburb', 'province', 'street_address',
            'property_type', 'custom_property_type', 'display_property_type',
            'bedrooms', 'bathrooms', 'parking_spaces', 'listing_price',
            'is_pet_friendly', 'has_pool', 'is_active', 'is_featured',
            'images', 'agent_name', 'agent_email', 'agent_phone',
            'created_at', 'updated_at', 'published_at', 'view_count'
        ]
        read_only_fields = [
            'id', 'agent_name', 'agent_email', 'agent_phone',
            'created_at', 'updated_at', 'published_at', 'view_count'
        ]

class PropertyListingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new property listings"""
    images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
        write_only=True
    )
    
    class Meta:
        model = PropertyListing
        fields = [
            'title', 'description', 'suburb', 'province', 'street_address',
            'property_type', 'custom_property_type', 'bedrooms', 'bathrooms',
            'parking_spaces', 'listing_price', 'is_pet_friendly', 'has_pool',
            'is_featured', 'agent', 'images'
        ]
        extra_kwargs = {
            'agent': {'required': False}
        }
    
    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        # Set agent to current user if not provided
        if 'agent' not in validated_data:
            validated_data['agent'] = self.context['request'].user
        property_listing = PropertyListing.objects.create(**validated_data)
        
        # Create property images
        for i, image_data in enumerate(images_data):
            PropertyImage.objects.create(
                property=property_listing,
                image=image_data,
                is_primary=(i == 0),  # First image is primary
                order=i
            )
        
        return property_listing

class PropertyListingUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating property listings"""
    images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
        write_only=True
    )
    
    class Meta:
        model = PropertyListing
        fields = [
            'title', 'description', 'suburb', 'province', 'street_address',
            'property_type', 'custom_property_type', 'bedrooms', 'bathrooms',
            'parking_spaces', 'listing_price', 'is_pet_friendly', 'has_pool',
            'is_active', 'is_featured', 'agent', 'images'
        ]
        extra_kwargs = {
            'agent': {'required': False}
        }
    
    def update(self, instance, validated_data):
        images_data = validated_data.pop('images', None)
        
        # Update the property listing
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update images if provided
        if images_data is not None:
            # Delete existing images
            instance.images.all().delete()
            
            # Create new images
            for i, image_data in enumerate(images_data):
                PropertyImage.objects.create(
                    property=instance,
                    image=image_data,
                    is_primary=(i == 0),  # First image is primary
                    order=i
                )
        
        return instance

class PropertyImageUploadSerializer(serializers.ModelSerializer):
    """Serializer for uploading additional images to a property"""
    
    class Meta:
        model = PropertyImage
        fields = ['image', 'alt_text', 'is_primary']
    
    def create(self, validated_data):
        property_id = self.context.get('property_id')
        property_listing = PropertyListing.objects.get(id=property_id)
        
        # If this image is set as primary, unset others
        if validated_data.get('is_primary', False):
            PropertyImage.objects.filter(property=property_listing).update(is_primary=False)
        
        return PropertyImage.objects.create(property=property_listing, **validated_data) 