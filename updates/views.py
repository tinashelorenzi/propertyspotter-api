from django.shortcuts import render
from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Update
from .serializers import UpdateSerializer
from .services import WhatsAppService
from django.shortcuts import get_object_or_404
from users.models import CustomUser
import logging
from rest_framework.permissions import BasePermission
from django_filters import rest_framework as django_filters
from rest_framework.exceptions import NotFound

logger = logging.getLogger(__name__)

class UpdateFilter(django_filters.FilterSet):
    update_type = django_filters.ChoiceFilter(choices=Update.UpdateType.choices)
    delivery_status = django_filters.ChoiceFilter(choices=Update.DeliveryStatus.choices)
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = Update
        fields = ['update_type', 'delivery_status', 'created_after', 'created_before']

class CanAccessUpdates(BasePermission):
    """
    Custom permission to only allow users to access their own updates
    or admins to access any updates
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Allow admins to access any update
        if request.user.role == 'Admin':
            return True
        # Users can only access their own updates
        return obj.recipient == request.user

# Create your views here.

class UpdateCreateView(generics.CreateAPIView):
    queryset = Update.objects.all()
    serializer_class = UpdateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # Debug logging
        recipient_id = request.data.get('recipient')
        logger.info(f"Attempting to create update for recipient: {recipient_id}")
        
        # Check if user exists
        try:
            user = CustomUser.objects.get(id=recipient_id)
            logger.info(f"Found user: {user.email}, role: {user.role}")
        except CustomUser.DoesNotExist:
            logger.error(f"User with ID {recipient_id} does not exist")
            return Response(
                {"error": f"User with ID {recipient_id} does not exist"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create the update
        update = serializer.save()
        
        # Get the recipient's phone number
        recipient = get_object_or_404(CustomUser, id=update.recipient.id)
        if not recipient.phone:
            return Response(
                {"error": "Recipient does not have a phone number"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Initialize WhatsApp service
        whatsapp_service = WhatsAppService()
        
        # Send WhatsApp message
        result = whatsapp_service.send_message(
            to_number=recipient.phone,
            message=f"{update.title}\n\n{update.message}"
        )
        
        if result['success']:
            # Update the delivery status
            update.mark_as_sent(result['message_sid'])
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            # Mark as failed if sending failed
            update.mark_as_failed()
            return Response(
                {
                    "error": "Failed to send WhatsApp message",
                    "details": result['error'],
                    "update": serializer.data
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UserUpdatesListView(generics.ListAPIView):
    serializer_class = UpdateSerializer
    permission_classes = [IsAuthenticated, CanAccessUpdates]
    filter_backends = [django_filters.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = UpdateFilter
    search_fields = ['title', 'message']
    ordering_fields = ['created_at', 'delivery_status']
    ordering = ['-created_at']

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        logger.info(f"Fetching updates for user_id: {user_id}")
        logger.info(f"Requesting user: {self.request.user.id}, role: {self.request.user.role}")
        
        # First check if the target user exists
        try:
            target_user = CustomUser.objects.get(id=user_id)
            logger.info(f"Target user found: {target_user.email}")
        except CustomUser.DoesNotExist:
            logger.error(f"User with ID {user_id} does not exist")
            raise NotFound(detail=f"User with ID {user_id} does not exist")
        
        # Base queryset excluding failed updates
        base_queryset = Update.objects.exclude(
            delivery_status=Update.DeliveryStatus.FAILED
        )
        
        # If user is admin, they can view any user's updates
        if self.request.user.role == 'Admin':
            logger.info("Admin user accessing updates")
            return base_queryset.filter(recipient_id=user_id)
        
        # Regular users can only view their own updates
        # Convert both IDs to strings for comparison
        if str(self.request.user.id) != str(user_id):
            logger.warning(f"User {self.request.user.id} attempted to access updates for user {user_id}")
            raise NotFound(detail="You don't have permission to view these updates")
            
        logger.info(f"User {self.request.user.id} accessing their own updates")
        return base_queryset.filter(recipient=self.request.user)

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            page = self.paginate_queryset(queryset)
            
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'status': 'success',
                'data': serializer.data,
                'message': 'Updates retrieved successfully'
            })
        except NotFound as e:
            return Response({
                'status': 'error',
                'message': str(e.detail)
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error fetching updates: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'An error occurred while fetching updates'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
