from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import ContactEntry
from .serializers import ContactEntrySerializer
import logging

logger = logging.getLogger(__name__)

# Create your views here.

class ContactEntryView(generics.CreateAPIView):
    """
    View for handling contact form submissions
    """
    queryset = ContactEntry.objects.all()
    serializer_class = ContactEntrySerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Save the contact entry
            contact_entry = serializer.save()
            
            # Prepare email content using template
            context = {
                'contact': contact_entry
            }
            html_message = render_to_string('contact/email/contact_notification.html', context)
            plain_message = strip_tags(html_message)
            
            # Send notification email to admin
            send_mail(
                subject=f"New Contact Form Submission from {contact_entry.name}",
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"Contact form submission from {contact_entry.email} processed successfully")
            
            return Response({
                'status': 'success',
                'message': 'Thank you for your message. We will get back to you soon.',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error processing contact form submission: {str(e)}")
            # Still save the contact entry even if email fails
            if 'contact_entry' not in locals():
                contact_entry = serializer.save()
            
            return Response({
                'status': 'success',  # Return success to user even if email fails
                'message': 'Thank you for your message. We will get back to you soon.',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
