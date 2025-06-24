from django.contrib import admin
from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from users.models import AdminLoginAttempt
import logging

logger = logging.getLogger(__name__)

class RateLimitedAdminAuthenticationForm(AdminAuthenticationForm):
    """
    Custom authentication form with rate limiting
    """
    
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        
        if username and password:
            # Get client IP from request
            request = getattr(self, 'request', None)
            if request:
                client_ip = self.get_client_ip(request)
            else:
                client_ip = '127.0.0.1'  # Fallback for local development
            
            # Check if IP is locked out
            if self.is_ip_locked_out(client_ip):
                logger.warning(f"Admin login attempt from locked out IP: {client_ip}")
                raise self.get_invalid_login_error()
            
            # Check if username is locked out
            if self.is_username_locked_out(username):
                logger.warning(f"Admin login attempt for locked out username: {username}")
                raise self.get_invalid_login_error()
            
            # Authenticate user
            self.user_cache = authenticate(self.request, username=username, password=password)
            
            # Record the login attempt
            success = self.user_cache is not None
            AdminLoginAttempt.objects.create(
                ip_address=client_ip,
                username=username,
                success=success
            )
            
            if self.user_cache is None:
                logger.warning(f"Failed admin login attempt for username: {username} from IP: {client_ip}")
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)
                logger.info(f"Successful admin login for username: {username} from IP: {client_ip}")
        
        return cleaned_data
    
    def get_client_ip(self, request):
        """
        Get the client IP address from the request
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def is_ip_locked_out(self, ip_address):
        """
        Check if an IP address is locked out due to too many failed attempts
        """
        # Check for failed attempts in the last 10 minutes
        cutoff_time = timezone.now() - timedelta(minutes=10)
        failed_attempts = AdminLoginAttempt.objects.filter(
            ip_address=ip_address,
            success=False,
            attempted_at__gte=cutoff_time
        ).count()
        
        return failed_attempts >= 6
    
    def is_username_locked_out(self, username):
        """
        Check if a username is locked out due to too many failed attempts
        """
        # Check for failed attempts in the last 10 minutes
        cutoff_time = timezone.now() - timedelta(minutes=10)
        failed_attempts = AdminLoginAttempt.objects.filter(
            username=username,
            success=False,
            attempted_at__gte=cutoff_time
        ).count()
        
        return failed_attempts >= 6

class RateLimitedAdminSite(admin.AdminSite):
    """
    Custom admin site with rate limiting
    """
    login_form = RateLimitedAdminAuthenticationForm

# Create the custom admin site instance
admin_site = RateLimitedAdminSite(name='rate_limited_admin')

# Import and register all models from existing apps
from users.models import CustomUser, Agency, VerificationToken, InvitationToken, AdminLoginAttempt
from users.admin import CustomUserAdmin, AgencyAdmin, VerificationTokenAdmin, InvitationTokenAdmin, AdminLoginAttemptAdmin
from blog.models import BlogPost, BlogCategory
from blog.admin import BlogPostAdmin, BlogCategoryAdmin
from contact.models import ContactEntry
from contact.admin import ContactEntryAdmin
from leads.models import Lead, LeadImage
from leads.admin import LeadAdmin, LeadImageAdmin
from listings.models import PropertyListing, PropertyImage
from listings.admin import PropertyListingAdmin, PropertyImageAdmin
from updates.models import Update
from updates.admin import UpdateAdmin
from properties.models import Property
from properties.admin import PropertyAdmin
from commissions.models import Commission
from commissions.admin import CommissionAdmin

# Register all models with the custom admin site
admin_site.register(CustomUser, CustomUserAdmin)
admin_site.register(Agency, AgencyAdmin)
admin_site.register(VerificationToken, VerificationTokenAdmin)
admin_site.register(InvitationToken, InvitationTokenAdmin)
admin_site.register(AdminLoginAttempt, AdminLoginAttemptAdmin)
admin_site.register(BlogPost, BlogPostAdmin)
admin_site.register(BlogCategory, BlogCategoryAdmin)
admin_site.register(ContactEntry, ContactEntryAdmin)
admin_site.register(Lead, LeadAdmin)
admin_site.register(LeadImage, LeadImageAdmin)
admin_site.register(PropertyListing, PropertyListingAdmin)
admin_site.register(PropertyImage, PropertyImageAdmin)
admin_site.register(Update, UpdateAdmin)
admin_site.register(Property, PropertyAdmin)
admin_site.register(Commission, CommissionAdmin) 