from django.db import models
from django.conf import settings
from leads.models import Lead

class Commission(models.Model):
    """
    Model for tracking commission payments
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='commissions')
    spotter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='earned_commissions',
        limit_choices_to={'role': 'Spotter'}
    )
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='paid_commissions',
        limit_choices_to={'role': 'Agent'}
    )
    
    # Commission amounts
    total_commission_amount = models.DecimalField(max_digits=10, decimal_places=2)
    spotter_commission_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Payment tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_date = models.DateField(null=True, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Commission for {self.lead} - {self.status}"

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Calculate spotter commission amount if not set
        if not self.spotter_commission_amount and self.lead.spotter_commission_percentage:
            self.spotter_commission_amount = (
                self.total_commission_amount * 
                (self.lead.spotter_commission_percentage / 100)
            )
        super().save(*args, **kwargs) 