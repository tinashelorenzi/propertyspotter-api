from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class Update(models.Model):
    class UpdateType(models.TextChoices):
        LEAD_STATUS = 'LEAD_STATUS', _('Lead Status Update')
        COMMISSION = 'COMMISSION', _('Commission Update')
        PAYMENT = 'PAYMENT', _('Payment Update')
        SYSTEM = 'SYSTEM', _('System Update')
        OTHER = 'OTHER', _('Other')

    class DeliveryStatus(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        SENT = 'SENT', _('Sent')
        DELIVERED = 'DELIVERED', _('Delivered')
        READ = 'READ', _('Read')
        FAILED = 'FAILED', _('Failed')

    # Basic update information
    title = models.CharField(max_length=200)
    message = models.TextField()
    update_type = models.CharField(
        max_length=20,
        choices=UpdateType.choices,
        default=UpdateType.OTHER
    )
    
    # Recipient information
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='updates',
        limit_choices_to={'role': 'Spotter'},  # Updated to match the correct case
        to_field='id'  # This ensures we use the UUID field
    )
    
    # Delivery tracking
    delivery_status = models.CharField(
        max_length=20,
        choices=DeliveryStatus.choices,
        default=DeliveryStatus.PENDING
    )
    whatsapp_message_id = models.CharField(max_length=100, blank=True, null=True)
    delivery_attempts = models.PositiveIntegerField(default=0)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    
    # Related objects (optional)
    related_lead = models.ForeignKey(
        'leads.Lead',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updates'
    )
    related_commission = models.ForeignKey(
        'commissions.Commission',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updates'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'delivery_status']),
            models.Index(fields=['update_type', 'created_at']),
        ]

    def __str__(self):
        return f"{self.update_type} - {self.recipient.email} - {self.created_at}"

    def mark_as_sent(self, whatsapp_message_id):
        """Mark the update as sent and store the WhatsApp message ID."""
        self.delivery_status = self.DeliveryStatus.SENT
        self.whatsapp_message_id = whatsapp_message_id
        self.delivery_attempts += 1
        self.last_attempt_at = timezone.now()
        self.save()

    def mark_as_delivered(self):
        """Mark the update as delivered."""
        self.delivery_status = self.DeliveryStatus.DELIVERED
        self.delivered_at = timezone.now()
        self.save()

    def mark_as_read(self):
        """Mark the update as read."""
        self.delivery_status = self.DeliveryStatus.READ
        self.read_at = timezone.now()
        self.save()

    def mark_as_failed(self):
        """Mark the update as failed."""
        self.delivery_status = self.DeliveryStatus.FAILED
        self.delivery_attempts += 1
        self.last_attempt_at = timezone.now()
        self.save()
