from django.contrib import admin
from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.conf import settings
from security_handler.turnstile import verify_turnstile_token
import logging

logger = logging.getLogger(__name__)

class TurnstileAdminAuthenticationForm(AdminAuthenticationForm):
    """
    Custom authentication form that includes Turnstile verification
    """
    
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        
        if username and password:
            # Verify Turnstile token
            turnstile_response = self.data.get('cf-turnstile-response')
            if not turnstile_response:
                raise self.get_invalid_login_error()
            
            # Get client IP from request
            request = getattr(self, 'request', None)
            if request:
                client_ip = self.get_client_ip(request)
            else:
                client_ip = '127.0.0.1'  # Fallback for local development
            
            # Verify the Turnstile token
            if not verify_turnstile_token(turnstile_response, client_ip):
                logger.warning(f"Invalid Turnstile token for admin login attempt from IP: {client_ip}")
                raise self.get_invalid_login_error()
            
            # Authenticate user
            self.user_cache = authenticate(self.request, username=username, password=password)
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)
        
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

class TurnstileAdminSite(admin.AdminSite):
    """
    Custom admin site with Turnstile verification
    """
    login_form = TurnstileAdminAuthenticationForm
    
    def login(self, request, extra_context=None):
        """
        Override the login method to add Turnstile site key to context
        """
        extra_context = extra_context or {}
        turnstile_site_key = getattr(settings, 'TURNSTILE_SITE_KEY', '')
        extra_context['turnstile_site_key'] = turnstile_site_key
        logger.info(f"Turnstile site key: {turnstile_site_key}")
        return super().login(request, extra_context)

# Create the custom admin site instance
admin_site = TurnstileAdminSite(name='turnstile_admin')

# Import and register all models from existing apps
from users.models import CustomUser, Agency, VerificationToken, InvitationToken
from users.admin import CustomUserAdmin, AgencyAdmin, VerificationTokenAdmin, InvitationTokenAdmin
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