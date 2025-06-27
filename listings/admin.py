from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django import forms
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from .models import PropertyListing, PropertyImage
from .widgets import MultipleImagePreviewWidget


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 0  # Don't show extra empty forms since we'll use bulk upload
    fields = ('image_preview', 'image', 'alt_text', 'is_primary', 'order')
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 60px; max-width: 60px; border-radius: 4px;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = 'Preview'
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.form.base_fields['is_primary'].help_text = "Check this to make this the primary image"
        return formset


class PropertyListingAdminForm(forms.ModelForm):
    """Custom form with multiple image upload field"""
    
    bulk_images = forms.FileField(
        widget=MultipleImagePreviewWidget(),
        required=False,
        help_text="Select multiple images at once. Hold Ctrl/Cmd to select multiple files.",
        label="Bulk Upload Images"
    )
    
    class Meta:
        model = PropertyListing
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'cols': 80}),
            'street_address': forms.TextInput(attrs={'size': 60}),
            'listing_price': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Move bulk_images field to the top for better UX
        if 'bulk_images' in self.fields:
            bulk_images_field = self.fields.pop('bulk_images')
            # Insert at the beginning
            new_fields = {'bulk_images': bulk_images_field}
            new_fields.update(self.fields)
            self.fields = new_fields

@admin.register(PropertyListing)
class PropertyListingAdmin(admin.ModelAdmin):
    form = PropertyListingAdminForm
    list_display = ('title', 'suburb', 'province', 'listing_price', 'agent_display', 'is_active', 'is_featured', 'view_count', 'image_count', 'image_preview')
    list_filter = ('province', 'property_type', 'is_active', 'is_featured', 'is_pet_friendly', 'has_pool', 'created_at', 'agent')
    search_fields = ('title', 'description', 'suburb', 'street_address', 'agent__email', 'agent__first_name', 'agent__last_name')
    readonly_fields = ('id', 'view_count', 'created_at', 'updated_at', 'published_at', 'primary_image_display', 'images_summary')
    inlines = [PropertyImageInline]
    list_editable = ('is_active', 'is_featured')
    list_per_page = 20
    
    fieldsets = (
        ('Bulk Image Upload', {
            'fields': ('bulk_images',),
            'classes': ('wide',),
            'description': 'Upload multiple images at once using the field below. Individual images can still be managed in the "Images" section at the bottom of this page.'
        }),
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
        ('Current Images Summary', {
            'fields': ('images_summary',),
            'classes': ('collapse',)
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
        return super().get_queryset(request).select_related('agent').prefetch_related('images')
    
    def agent_display(self, obj):
        """Display agent name or 'No Agent' if not assigned"""
        if obj.agent:
            return f"{obj.agent.get_full_name() or obj.agent.email}"
        return format_html('<span style="color: #999;">No Agent</span>')
    agent_display.short_description = 'Agent'
    
    def image_count(self, obj):
        """Display the number of images"""
        count = obj.images.count()
        if count > 0:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">{} image{}</span>',
                count,
                's' if count != 1 else ''
            )
        return format_html('<span style="color: #dc3545;">No images</span>')
    image_count.short_description = 'Images'
    
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
    
    def images_summary(self, obj):
        """Show a summary of all images"""
        images = obj.images.all()
        if not images:
            return format_html('<p style="color: #999;">No images uploaded yet.</p>')
        
        html = '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 10px; max-height: 400px; overflow-y: auto; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">'
        
        for image in images:
            primary_badge = ''
            if image.is_primary:
                primary_badge = '<div style="position: absolute; top: 2px; right: 2px; background: #28a745; color: white; padding: 2px 4px; border-radius: 2px; font-size: 10px;">PRIMARY</div>'
            
            html += f'''
                <div style="position: relative; border: 1px solid #eee; border-radius: 4px; overflow: hidden;">
                    {primary_badge}
                    <img src="{image.image.url}" style="width: 100%; height: 80px; object-fit: cover;" />
                    <div style="padding: 4px; font-size: 10px; background: #f8f9fa;">
                        Order: {image.order}
                    </div>
                </div>
            '''
        
        html += '</div>'
        html += f'<p style="margin-top: 10px; font-weight: bold;">Total: {images.count()} images</p>'
        
        return format_html(html)
    images_summary.short_description = 'Images Overview'
    
    def save_model(self, request, obj, form, change):
        """Handle bulk image uploads"""
        # Save the main object first
        super().save_model(request, obj, form, change)
        
        # Handle bulk image uploads
        bulk_images = request.FILES.getlist('bulk_images')
        if bulk_images:
            self.process_bulk_images(obj, bulk_images, request)
    
    def process_bulk_images(self, property_listing, images, request):
        """Process multiple uploaded images"""
        # Get the current highest order number
        last_order = 0
        existing_images = property_listing.images.all()
        if existing_images:
            last_order = max(img.order for img in existing_images)
        
        # Check if there are no existing images to set the first as primary
        has_primary = property_listing.images.filter(is_primary=True).exists()
        
        created_count = 0
        for i, image_file in enumerate(images):
            try:
                # Validate that it's actually an image file
                if not image_file.content_type.startswith('image/'):
                    continue
                
                # Create new PropertyImage
                property_image = PropertyImage(
                    property=property_listing,
                    image=image_file,
                    order=last_order + i + 1,
                    is_primary=(not has_primary and i == 0),  # Set first image as primary if no primary exists
                    alt_text=f"Property image {last_order + i + 1}"
                )
                property_image.save()
                created_count += 1
                
                # After creating the first image, we have a primary
                if not has_primary and i == 0:
                    has_primary = True
                    
            except Exception as e:
                # Log the error but continue with other images
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error uploading image {image_file.name}: {str(e)}")
                continue
        
        # Add success message
        if created_count > 0:
            from django.contrib import messages
            messages.success(
                request,
                f"Successfully uploaded {created_count} image{'s' if created_count != 1 else ''}."
            )
    
    def get_form(self, request, obj=None, **kwargs):
        """Customize the form for better admin experience"""
        form_class = super().get_form(request, obj, **kwargs)
        
        # Create a new form class that ensures proper enctype
        class PropertyListingAdminFormWithEnctype(form_class):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                # Ensure the form can handle file uploads
                self.enctype = 'multipart/form-data'
        
        return PropertyListingAdminFormWithEnctype
    
    # Override to ensure form has proper enctype
    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context.update({
            'show_save_and_add_another': False,
            'show_save_and_continue': False,
        })
        return super().add_view(request, form_url, extra_context)
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context.update({
            'show_save_and_add_another': False,
            'show_save_and_continue': False,
        })
        return super().change_view(request, object_id, form_url, extra_context)
    
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