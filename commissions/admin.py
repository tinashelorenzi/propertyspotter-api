from django.contrib import admin
from .models import Commission

@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = ('lead', 'spotter', 'agent', 'total_commission_amount', 
                   'spotter_commission_amount', 'status', 'payment_date')
    list_filter = ('status', 'spotter', 'agent', 'payment_date', 'created_at')
    search_fields = ('lead__first_name', 'lead__last_name', 'payment_reference')
    readonly_fields = ('created_at', 'updated_at', 'approved_at', 'paid_at')
    
    fieldsets = (
        ('Lead Information', {
            'fields': ('lead', 'spotter', 'agent')
        }),
        ('Commission Details', {
            'fields': ('total_commission_amount', 'spotter_commission_amount')
        }),
        ('Payment Information', {
            'fields': ('status', 'payment_date', 'payment_reference')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'approved_at', 'paid_at'),
            'classes': ('collapse',)
        }),
    ) 