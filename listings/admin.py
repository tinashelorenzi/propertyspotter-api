from django.contrib import admin
from django.utils.html import format_html
from django import forms
from django.forms.widgets import Widget
from django.utils.safestring import mark_safe
from .models import PropertyListing, PropertyImage


class MultipleFileInput(Widget):
    """Custom widget that supports multiple file selection"""
    
    def __init__(self, attrs=None):
        if attrs is None:
            attrs = {}
        super().__init__(attrs)
    
    def render(self, name, value, attrs=None, renderer=None):
        if attrs is None:
            attrs = {}
        
        # Add required attributes for multiple file input
        attrs.update({
            'type': 'file',
            'multiple': True,
            'accept': 'image/*'
        })
        
        # Build the attribute string
        attr_str = ' '.join([f'{k}="{v}"' for k, v in attrs.items()])
        
        html = f'<input name="{name}" {attr_str}>'
        return mark_safe(html)
    
    def value_from_datadict(self, data, files, name):
        """Get multiple files from the uploaded data"""
        upload = files.getlist(name)
        if not upload:
            return None
        return upload

class MultipleFileField(forms.Field):
    """Custom field that handles multiple file uploads"""
    
    widget = MultipleFileInput
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def clean(self, data, initial=None):
        if not data and not self.required:
            return []
        
        if not data:
            return []
            
        if not isinstance(data, list):
            data = [data]
        
        result = []
        for uploaded_file in data:
            if uploaded_file:
                # Basic validation
                if hasattr(uploaded_file, 'content_type'):
                    if not uploaded_file.content_type.startswith('image/'):
                        continue
                result.append(uploaded_file)
        
        return result


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1
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


class PropertyListingAdminForm(forms.ModelForm):
    """Custom form with bulk image upload"""
    
    # Use our custom MultipleFileField
    bulk_images = MultipleFileField(
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
        # Move bulk_images field to the top
        if 'bulk_images' in self.fields:
            bulk_images_field = self.fields.pop('bulk_images')
            new_fields = {'bulk_images': bulk_images_field}
            new_fields.update(self.fields)
            self.fields = new_fields


@admin.register(PropertyListing)
class PropertyListingAdmin(admin.ModelAdmin):
    form = PropertyListingAdminForm
    list_display = ('title', 'suburb', 'province', 'listing_price', 'agent_display', 'is_active', 'is_featured', 'view_count', 'image_count')
    list_filter = ('province', 'property_type', 'is_active', 'is_featured', 'is_pet_friendly', 'has_pool', 'created_at', 'agent')
    search_fields = ('title', 'description', 'suburb', 'street_address', 'agent__email', 'agent__first_name', 'agent__last_name')
    readonly_fields = ('id', 'view_count', 'created_at', 'updated_at', 'published_at', 'images_summary')
    inlines = [PropertyImageInline]
    list_editable = ('is_active', 'is_featured')
    list_per_page = 20
    
    fieldsets = (
        ('Bulk Image Upload', {
            'fields': ('bulk_images',),
            'classes': ('wide',),
            'description': 'Upload multiple images at once. Hold Ctrl/Cmd to select multiple files.'
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
        ('Agent Assignment', {
            'fields': ('agent',),
            'classes': ('wide',)
        }),
        ('Current Images', {
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
        
        # Debug: Print comprehensive information
        print(f"\n=== BULK IMAGE UPLOAD DEBUG ===")
        print(f"Form is valid: {form.is_valid()}")
        print(f"Form errors: {form.errors}")
        print(f"Request method: {request.method}")
        print(f"Content-Type: {request.content_type}")
        print(f"POST data keys: {list(request.POST.keys())}")
        print(f"FILES data keys: {list(request.FILES.keys())}")
        
        # Print all FILES for debugging
        for key, file_obj in request.FILES.items():
            print(f"FILE '{key}': {file_obj.name} ({file_obj.size} bytes)")
        
        # Try getlist for bulk_images
        file_list = request.FILES.getlist('bulk_images')
        print(f"request.FILES.getlist('bulk_images'): {len(file_list)} files")
        for i, f in enumerate(file_list):
            print(f"  File {i}: {f.name} ({f.size} bytes)")
        
        # Check form cleaned_data
        if hasattr(form, 'cleaned_data'):
            print(f"Form cleaned_data keys: {list(form.cleaned_data.keys())}")
            if 'bulk_images' in form.cleaned_data:
                bulk_images = form.cleaned_data['bulk_images']
                print(f"Form cleaned_data bulk_images: {bulk_images}")
                print(f"Type: {type(bulk_images)}")
                print(f"Length: {len(bulk_images) if bulk_images else 0}")
                
                if bulk_images and len(bulk_images) > 0:
                    print(f"Processing {len(bulk_images)} images from form.cleaned_data")
                    self.process_bulk_images(obj, bulk_images, request)
                else:
                    print("No images in cleaned_data")
            else:
                print("'bulk_images' not found in form.cleaned_data")
        else:
            print("Form has no cleaned_data")
        
        print(f"=== END DEBUG ===\n")
    
    def process_bulk_images(self, property_listing, images, request):
        """Process multiple uploaded images"""
        print(f"Processing {len(images)} images for property {property_listing.id}")
        
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
                print(f"Processing image {i+1}: {image_file.name}, type: {image_file.content_type}")
                
                # Validate that it's actually an image file
                if not image_file.content_type.startswith('image/'):
                    print(f"Skipping non-image file: {image_file.name}")
                    continue
                
                # Create new PropertyImage
                property_image = PropertyImage(
                    property=property_listing,
                    image=image_file,
                    order=last_order + i + 1,
                    is_primary=(not has_primary and i == 0),
                    alt_text=f"Property image {last_order + i + 1}"
                )
                property_image.save()
                created_count += 1
                print(f"Created PropertyImage {property_image.id}")
                
                # After creating the first image, we have a primary
                if not has_primary and i == 0:
                    has_primary = True
                    
            except Exception as e:
                print(f"Error uploading image {image_file.name}: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
        
        # Add success message
        if created_count > 0:
            from django.contrib import messages
            messages.success(
                request,
                f"Successfully uploaded {created_count} image{'s' if created_count != 1 else ''}."
            )
            print(f"Successfully created {created_count} images")
        else:
            print("No images were created")


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