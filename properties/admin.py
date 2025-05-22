from django.contrib import admin
from .models import Property, PropertyImage

class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('title', 'address', 'price', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'address', 'description')
    inlines = [PropertyImageInline]
    readonly_fields = ('created_at', 'updated_at')

@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ('property', 'image', 'is_primary', 'created_at')
    list_filter = ('is_primary', 'created_at')
    readonly_fields = ('created_at',) 