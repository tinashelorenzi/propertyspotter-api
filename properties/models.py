from django.db import models
from django.conf import settings

class Property(models.Model):
    """
    Property model for storing property information
    """
    PROPERTY_TYPES = [
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('land', 'Land'),
        ('industrial', 'Industrial'),
    ]

    STATUS_CHOICES = [
        ('available', 'Available'),
        ('sold', 'Sold'),
        ('pending', 'Pending'),
        ('off_market', 'Off Market'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    price = models.DecimalField(max_digits=12, decimal_places=2)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    bedrooms = models.IntegerField(null=True, blank=True)
    bathrooms = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    square_feet = models.IntegerField(null=True, blank=True)
    lot_size = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    year_built = models.IntegerField(null=True, blank=True)
    listing_url = models.URLField(max_length=500, null=True, blank=True, help_text="URL where the property is listed (e.g., Property24, PrivateProperty)")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='properties')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.address}"

class PropertyImage(models.Model):
    """
    Model for storing property images
    """
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='properties/')
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.property.title}" 