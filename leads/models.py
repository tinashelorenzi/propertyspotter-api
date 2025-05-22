from django.db import models
from django.conf import settings
from properties.models import Property

class Lead(models.Model):
    """
    Lead model for storing potential buyer/seller information
    """
    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('qualified', 'Qualified'),
        ('unqualified', 'Unqualified'),
        ('converted', 'Converted'),
        ('closed', 'Closed'),
    ]

    # Basic lead information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    notes_text = models.TextField(blank=True)
    
    # Property information (minimal, to be filled by agent)
    property = models.ForeignKey(Property, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads')
    
    # Spotter information (who found the lead)
    spotter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='spotted_leads',
        limit_choices_to={'role': 'Spotter'}
    )
    
    # Agent information (who is handling the lead)
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='handled_leads',
        limit_choices_to={'role': 'Agent'}
    )
    
    # Commission details
    agreed_commission_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Agreed commission percentage for this lead"
    )
    spotter_commission_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Percentage of commission that goes to the spotter"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.email}"

    class Meta:
        ordering = ['-created_at']

class LeadNote(models.Model):
    """
    Model for storing notes about leads
    """
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='notes')
    content = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Note for {self.lead} by {self.created_by}" 