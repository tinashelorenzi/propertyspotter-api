from django.contrib import admin
from .models import ContactEntry

@admin.register(ContactEntry)
class ContactEntryAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'message', 'created_at')
    search_fields = ('name', 'email', 'message')
    list_filter = ('created_at',)
