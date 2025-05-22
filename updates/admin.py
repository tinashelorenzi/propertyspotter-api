from django.contrib import admin
from .models import Update
from users.models import CustomUser

@admin.register(Update)
class UpdateAdmin(admin.ModelAdmin):
    list_display = ('title', 'recipient', 'update_type', 'delivery_status', 'created_at', 'delivered_at')
    list_filter = ('update_type', 'delivery_status', 'created_at')
    search_fields = ('title', 'message', 'recipient__email', 'recipient__username')
    readonly_fields = ('created_at', 'updated_at', 'delivered_at', 'read_at', 'last_attempt_at')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "recipient":
            kwargs["queryset"] = CustomUser.objects.filter(role='Spotter').order_by('email')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    fieldsets = (
        (None, {
            'fields': ('title', 'message', 'update_type', 'recipient')
        }),
        ('Delivery Information', {
            'fields': ('delivery_status', 'whatsapp_message_id', 'delivery_attempts', 'last_attempt_at')
        }),
        ('Related Objects', {
            'fields': ('related_lead', 'related_commission'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'delivered_at', 'read_at'),
            'classes': ('collapse',)
        }),
    )
