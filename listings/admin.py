from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django import forms
from .models import PropertyListing, PropertyImage

class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 3
    fields = ('image', 'alt_text', 'is_primary', 'order')
    readonly_fields = ('created_at',)
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.form.base_fields['is_primary'].help_text = "Check this to make this the primary image"
        return formset

class PropertyListingForm(forms.ModelForm):
    """Custom form for PropertyListing with better field organization"""
    
    class Meta:
        model = PropertyListing
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'cols': 80}),
            'street_address': forms.TextInput(attrs={'size': 60}),
            'listing_price': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
        }

@admin.register(PropertyListing)
class PropertyListingAdmin(admin.ModelAdmin):
    form = PropertyListingForm
    list_display = ('title', 'suburb', 'province', 'listing_price', 'agent_display', 'is_active', 'is_featured', 'view_count', 'image_preview')
    list_filter = ('province', 'property_type', 'is_active', 'is_featured', 'is_pet_friendly', 'has_pool', 'created_at', 'agent')
    search_fields = ('title', 'description', 'suburb', 'street_address', 'agent__email', 'agent__first_name', 'agent__last_name')
    readonly_fields = ('id', 'view_count', 'created_at', 'updated_at', 'published_at', 'primary_image_display')
    inlines = [PropertyImageInline]
    list_editable = ('is_active', 'is_featured')
    list_per_page = 20
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description'),
            'classes': ('wide',)
        }),
        ('Location Details', {
            'fields': ('suburb', 'province', 'street_address'),
            'classes': ('wide',)
        }),
        ('Property Specifications', {
            'fields': ('property_type', 'custom_property_type', 'bedrooms', 'bathrooms', 'parking_spaces'),
            'classes': ('wide',)
        }),
        ('Pricing', {
            'fields': ('listing_price',),
            'classes': ('wide',)
        }),
        ('Amenities & Features', {
            'fields': ('is_pet_friendly', 'has_pool'),
            'classes': ('wide',)
        }),
        ('Status & Visibility', {
            'fields': ('is_active', 'is_featured'),
            'classes': ('wide',)
        }),
        ('Agent Assignment (Optional)', {
            'fields': ('agent',),
            'classes': ('wide',),
            'description': 'You can optionally assign this property to a specific agent. Leave blank if no agent assignment is needed.'
        }),
        ('Analytics', {
            'fields': ('view_count',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('agent')
    
    def agent_display(self, obj):
        """Display agent name or 'No Agent' if not assigned"""
        if obj.agent:
            return f"{obj.agent.get_full_name() or obj.agent.email}"
        return format_html('<span style="color: #999;">No Agent</span>')
    agent_display.short_description = 'Agent'
    
    def image_preview(self, obj):
        """Show a small preview of the primary image in the list view"""
        primary_image = obj.primary_image
        if primary_image and primary_image.image:
            return format_html(
                '<img src="{}" style="max-height: 40px; max-width: 40px; border-radius: 4px;" />',
                primary_image.image.url
            )
        return format_html('<span style="color: #999;">No image</span>')
    image_preview.short_description = 'Image'
    
    def primary_image_display(self, obj):
        """Show the primary image in the detail view"""
        primary_image = obj.primary_image
        if primary_image and primary_image.image:
            return format_html(
                '<img src="{}" style="max-height: 200px; max-width: 300px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />',
                primary_image.image.url
            )
        return format_html('<span style="color: #999;">No primary image set</span>')
    primary_image_display.short_description = 'Primary Image'
    
    def save_model(self, request, obj, form, change):
        """Custom save method to handle agent assignment"""
        super().save_model(request, obj, form, change)
    
    def get_form(self, request, obj=None, **kwargs):
        """Customize the form for better admin experience"""
        form = super().get_form(request, obj, **kwargs)
        
        # Add help text for better guidance
        form.base_fields['title'].help_text = "Enter a descriptive title for the property"
        form.base_fields['description'].help_text = "Provide a detailed description of the property"
        form.base_fields['listing_price'].help_text = "Enter the price in Rands (e.g., 2500000.00)"
        form.base_fields['custom_property_type'].help_text = "Use this field if the property type is not in the dropdown list"
        form.base_fields['agent'].help_text = "Optional: Assign this property to a specific agent. Leave blank if no agent assignment is needed."
        
        return form
    
    actions = ['make_active', 'make_inactive', 'make_featured', 'remove_featured']
    
    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} properties have been activated.')
    make_active.short_description = "Activate selected properties"
    
    def make_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} properties have been deactivated.')
    make_inactive.short_description = "Deactivate selected properties"
    
    def make_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} properties have been marked as featured.')
    make_featured.short_description = "Mark selected properties as featured"
    
    def remove_featured(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} properties have been removed from featured.')
    remove_featured.short_description = "Remove selected properties from featured"

@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ('property', 'image_preview', 'is_primary', 'order', 'created_at')
    list_filter = ('is_primary', 'created_at', 'property__province', 'property__suburb')
    search_fields = ('property__title', 'alt_text', 'property__suburb')
    readonly_fields = ('created_at', 'image_preview_large')
    list_editable = ('is_primary', 'order')
    
    fieldsets = (
        ('Image Information', {
            'fields': ('property', 'image', 'alt_text')
        }),
        ('Display Settings', {
            'fields': ('is_primary', 'order')
        }),
        ('Preview', {
            'fields': ('image_preview_large',),
            'classes': ('wide',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px; border-radius: 4px;" />',
                obj.image.url
            )
        return format_html('<span style="color: #999;">No image</span>')
    image_preview.short_description = 'Preview'
    
    def image_preview_large(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 300px; max-width: 400px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />',
                obj.image.url
            )
        return format_html('<span style="color: #999;">No image uploaded</span>')
    image_preview_large.short_description = 'Image Preview'
