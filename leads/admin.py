from django.contrib import admin
from .models import Lead, LeadImage, LeadNote

class LeadImageInline(admin.TabularInline):
    model = LeadImage
    extra = 1

class LeadNoteInline(admin.TabularInline):
    model = LeadNote
    extra = 1

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = (
        'first_name', 'last_name', 'email', 'phone', 'status',
        'spotter', 'agent', 'assigned_agency', 'requested_agent',
        'agreed_commission_amount', 'spotter_commission_amount',
        'created_at', 'assigned_at', 'closed_at'
    )
    list_filter = (
        'status', 'created_at', 'assigned_at', 'closed_at',
        'spotter', 'agent', 'assigned_agency', 'requested_agent'
    )
    search_fields = (
        'first_name', 'last_name', 'email', 'phone',
        'spotter__email', 'agent__email', 'assigned_agency__name',
        'requested_agent__email'
    )
    inlines = [LeadImageInline, LeadNoteInline]
    readonly_fields = ('created_at', 'updated_at', 'assigned_at', 'closed_at')
    fieldsets = (
        (None, {
            'fields': (
                'first_name', 'last_name', 'email', 'phone', 'status',
                'spotter', 'agent', 'assigned_agency', 'requested_agent',
                'notes_text', 'agreed_commission_amount', 'spotter_commission_amount',
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'assigned_at', 'closed_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(LeadImage)
class LeadImageAdmin(admin.ModelAdmin):
    list_display = ('lead', 'image', 'description', 'uploaded_at')
    search_fields = ('lead__first_name', 'lead__last_name', 'description')
    list_filter = ('uploaded_at',)

@admin.register(LeadNote)
class LeadNoteAdmin(admin.ModelAdmin):
    list_display = ('lead', 'created_by', 'created_at')
    search_fields = ('lead__first_name', 'lead__last_name', 'content', 'created_by__email')
    list_filter = ('created_at',) 