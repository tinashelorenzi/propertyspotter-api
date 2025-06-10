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
    list_display = ('id', 'first_name', 'last_name', 'email', 'phone', 'street_address', 'suburb', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('first_name', 'last_name', 'email', 'phone', 'street_address', 'suburb', 'preferred_agent')
    inlines = [LeadImageInline, LeadNoteInline]
    readonly_fields = ('created_at', 'updated_at', 'assigned_at', 'accepted_at', 'closed_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'street_address', 'suburb', 'notes_text', 'preferred_agent')
        }),
        ('Status', {
            'fields': ('status', 'is_accepted')
        }),
        ('Relationships', {
            'fields': ('spotter', 'agent', 'requested_agent', 'assigned_agency', 'property')
        }),
        ('Commission', {
            'fields': ('agreed_commission_amount', 'spotter_commission_amount', 'platform_fee')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'assigned_at', 'accepted_at', 'closed_at')
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