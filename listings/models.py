from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse
import uuid

def property_image_upload_path(instance, filename):
    """Generate upload path for property images"""
    return f'properties/{instance.property.id}/{filename}'

class PropertyListing(models.Model):
    """Property listing model"""
    
    PROPERTY_TYPE_CHOICES = [
        ('house', 'House'),
        ('apartment', 'Apartment'),
        ('townhouse', 'Townhouse'),
        ('duplex', 'Duplex'),
        ('penthouse', 'Penthouse'),
        ('studio', 'Studio'),
        ('cottage', 'Cottage'),
        ('farm', 'Farm'),
        ('commercial', 'Commercial'),
        ('other', 'Other'),
    ]
    
    PROVINCE_CHOICES = [
        ('gauteng', 'Gauteng'),
        ('western_cape', 'Western Cape'),
        ('eastern_cape', 'Eastern Cape'),
        ('kwazulu_natal', 'KwaZulu-Natal'),
        ('free_state', 'Free State'),
        ('mpumalanga', 'Mpumalanga'),
        ('limpopo', 'Limpopo'),
        ('north_west', 'North West'),
        ('northern_cape', 'Northern Cape'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Location
    suburb = models.CharField(max_length=100)
    province = models.CharField(max_length=20, choices=PROVINCE_CHOICES)
    street_address = models.CharField(max_length=255)
    
    # Property Details
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES)
    custom_property_type = models.CharField(max_length=100, blank=True, help_text="Custom property type if not in the list")
    bedrooms = models.PositiveIntegerField()
    bathrooms = models.PositiveIntegerField()
    parking_spaces = models.PositiveIntegerField(default=0)
    
    # Pricing
    listing_price = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Amenities
    is_pet_friendly = models.BooleanField(default=False)
    has_pool = models.BooleanField(default=False)
    
    # Status and Publishing
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # Relationships (Optional)
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='property_listings',
        help_text="Optional: Assign to a specific agent"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(auto_now_add=True)
    
    # Analytics
    view_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-published_at', '-created_at']
        verbose_name = "Property Listing"
        verbose_name_plural = "Property Listings"
    
    def __str__(self):
        return f"{self.title} - {self.suburb}, {self.province}"
    
    def get_absolute_url(self):
        return reverse('listings:property_detail', kwargs={'id': self.id})
    
    def increment_view_count(self):
        """Increment the view count for this property"""
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    @property
    def display_property_type(self):
        """Return the property type to display"""
        if self.custom_property_type:
            return self.custom_property_type
        return self.get_property_type_display()
    
    @property
    def primary_image(self):
        """Get the primary image for this property"""
        return self.images.filter(is_primary=True).first() or self.images.first()

class PropertyImage(models.Model):
    """Images for property listings"""
    property = models.ForeignKey(
        PropertyListing,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to=property_image_upload_path)
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"Image for {self.property.title}"
    
    def save(self, *args, **kwargs):
        # If this image is set as primary, unset others
        if self.is_primary:
            PropertyImage.objects.filter(property=self.property).update(is_primary=False)
        super().save(*args, **kwargs)
