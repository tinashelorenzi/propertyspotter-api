from django.contrib import admin
from .models import Lead, LeadNote

class LeadNoteInline(admin.TabularInline):
    model = LeadNote
    extra = 1
    fields = ('content', 'created_by', 'created_at')
    readonly_fields = ('created_at',)

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'phone', 'status', 'spotter', 'agent', 'created_at')
    list_filter = ('status', 'spotter', 'agent', 'created_at')
    search_fields = ('first_name', 'last_name', 'email', 'phone')
    readonly_fields = ('created_at', 'updated_at', 'assigned_at', 'closed_at')
    inlines = [LeadNoteInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'status', 'notes_text')
        }),
        ('Property & Assignment', {
            'fields': ('property', 'spotter', 'agent')
        }),
        ('Commission Details', {
            'fields': ('agreed_commission_percentage', 'spotter_commission_percentage')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'assigned_at', 'closed_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(LeadNote)
class LeadNoteAdmin(admin.ModelAdmin):
    list_display = ('lead', 'content', 'created_by', 'created_at')
    list_filter = ('created_by', 'created_at')
    search_fields = ('content', 'lead__first_name', 'lead__last_name')
    readonly_fields = ('created_at',) 