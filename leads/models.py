from django.db import models
from django.conf import settings
from properties.models import Property
from django.utils import timezone
from users.models import CustomUser, Agency
from decimal import Decimal

class Lead(models.Model):
    """
    Lead model for storing potential buyer/seller information
    """
    STATUS_CHOICES = [
        ('new', 'New'),
        ('assigned', 'Assigned'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('closed', 'Closed'),
        ('rejected', 'Rejected')
    ]

    # Basic lead information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20)
    street_address = models.CharField(max_length=255, help_text="Street address of the property", null=True, blank=True)
    suburb = models.CharField(max_length=100, help_text="Suburb or town of the property", null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    notes_text = models.TextField(blank=True)
    is_accepted = models.BooleanField(default=False, help_text="Whether the agent has accepted this lead")
    preferred_agent = models.CharField(
        max_length=255, 
        blank=True, 
        help_text="Spotter's preferred agent (free text)"
    )
    
    # Property information (minimal, to be filled by agent)
    property = models.ForeignKey(Property, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads')
    
    # User relationships
    spotter = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='submitted_leads',
        null=True,  # Temporarily allow null for migration
        blank=True  # Temporarily allow blank for migration
    )
    agent = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_leads'
    )
    requested_agent = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requested_leads'
    )
    
    # Agency relationship
    assigned_agency = models.ForeignKey(
        Agency,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_leads'
    )
    
    # Commission fields
    agreed_commission_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    spotter_commission_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    def calculate_commissions(self):
        """
        Calculate spotter commission and platform fee based on agreed commission amount
        """
        if self.agreed_commission_amount is not None:
            # Calculate 7.5% of agreed commission
            total_deduction = self.agreed_commission_amount * Decimal('0.075')
            
            # 5% goes to spotter
            self.spotter_commission_amount = self.agreed_commission_amount * Decimal('0.05')
            
            # 2.5% goes to platform
            self.platform_fee = self.agreed_commission_amount * Decimal('0.025')
            
            self.save()

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.status}"

    def assign_to_agent(self, agent):
        self.agent = agent
        self.assigned_agency = agent.agency  # Set the assigned agency based on the agent's agency
        self.status = 'assigned'
        self.assigned_at = timezone.now()
        self.is_accepted = False  # Reset acceptance status when reassigned
        self.accepted_at = None
        self.save()

    def accept_lead(self):
        self.status = 'accepted'
        self.is_accepted = True
        self.accepted_at = timezone.now()
        self.save()

    def reject_lead(self):
        self.status = 'rejected'
        self.is_accepted = False
        self.accepted_at = None
        self.save()

    def close_lead(self):
        self.status = 'closed'
        self.closed_at = timezone.now()
        self.save()

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

class LeadImage(models.Model):
    """
    Model for storing images associated with leads
    """
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='leads/')
    description = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.lead} - {self.uploaded_at}" 