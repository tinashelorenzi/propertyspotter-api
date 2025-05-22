from django.db import models
from users.models import CustomUser
import uuid


# Property Types
class PropertyType(models.TextChoices):
    TOWNHOUSE = 'Townhouse', 'Townhouse'
    APARTMENT = 'Apartment', 'Apartment'
    HOUSE = 'House', 'House'
    COMMERCIAL = 'Commercial', 'Commercial'
    LAND = 'Land', 'Land'
    OTHER = 'Other', 'Other'


# Property Status
class PropertyStatus(models.TextChoices):
    NEW_SUBMISSION = 'New Submission', 'New Submission'
    UNSUCCESSFUL = 'Unsuccessful', 'Unsuccessful'
    PENDING_MANDATE = 'Pending Mandate', 'Pending Mandate'
    ALREADY_LISTED = 'Already Listed', 'Already Listed'
    LISTED = 'Listed', 'Listed'
    SOLD = 'Sold', 'Sold'
    COMMISSION_PAID = 'Commission Paid', 'Spotter Commission Paid'
    OWNER_NOT_FOUND = 'Owner Not Found', 'Owner Not Found'
    OTHER_SOLE_MANDATE = 'Other Sole Mandate', 'Other Sole Mandate'

class PropertyImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey('Property', related_name='property_images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='uploads/properties/images/')
    created_at = models.DateTimeField(auto_now_add=True)

# Property Model
class Property(models.Model):
    # Core Details
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    spotter = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="spotted_properties"
    )
    property_type = models.CharField(
        max_length=20, choices=PropertyType.choices, default=PropertyType.OTHER
    )
    status = models.CharField(
        max_length=30, choices=PropertyStatus.choices, default=PropertyStatus.NEW_SUBMISSION
    )
    owner_name = models.CharField(max_length=100, null=True, blank=True)
    owner_contact = models.CharField(max_length=20, null=True, blank=True)

    # Lead Source
    lead_source = models.CharField(max_length=255, null=True, blank=True)

    # Financials
    price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    commission = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # External References
    reference_name = models.CharField(max_length=100, null=True, blank=True)
    reference_details = models.TextField(null=True, blank=True)

    # Property Details
    total_bedrooms = models.IntegerField(default=0)
    total_bathrooms = models.IntegerField(default=0)

    # Address
    address = models.TextField(null=True, blank=True)

    # Images
    featured_image = models.ImageField(upload_to='uploads/properties/featured_images/', null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Notes
    spotter_notes = models.TextField(null=True, blank=True)
    agent_notes = models.TextField(null=True, blank=True)

    @property
    def image_urls(self):
        return [img.image.url for img in self.property_images.all()]

    def __str__(self):
        return f"{self.property_type} - {self.address or 'No Address'}"

    class Meta:
        ordering = ['-created_at']
