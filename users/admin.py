from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Agency, VerificationToken

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone', 'profile_image_url')}),
        ('Role & Agency', {'fields': ('role', 'agency')}),
        ('Banking Details', {'fields': ('bank_name', 'bank_branch_code', 'account_number', 'account_name', 'account_type')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'role'),
        }),
    )

@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'license_valid_until')
    search_fields = ('name', 'email', 'phone')
    list_filter = ('license_valid_until',)

@admin.register(VerificationToken)
class VerificationTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'created_at', 'used')
    search_fields = ('user__email', 'token')
    list_filter = ('used', 'created_at')
