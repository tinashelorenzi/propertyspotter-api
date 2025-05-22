from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Lead
from .serializers import LeadSubmissionSerializer, LeadListSerializer
from rest_framework.permissions import BasePermission
from django_filters import rest_framework as django_filters
from rest_framework.exceptions import NotFound
from users.models import CustomUser
import logging

logger = logging.getLogger(__name__)

class IsSpotter(BasePermission):
    """
    Custom permission to only allow spotters to submit leads
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'Spotter'

class LeadFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Lead.STATUS_CHOICES)
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    assigned = django_filters.BooleanFilter(field_name='agent', lookup_expr='isnull', exclude=True)

    class Meta:
        model = Lead
        fields = ['status', 'created_after', 'created_before', 'assigned']

class LeadSubmissionView(generics.CreateAPIView):
    serializer_class = LeadSubmissionSerializer
    permission_classes = [IsAuthenticated, IsSpotter]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        headers = self.get_success_headers(serializer.data)
        return Response({
            'status': 'success',
            'message': 'Lead submitted successfully',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED, headers=headers)

class SpotterLeadsListView(generics.ListAPIView):
    serializer_class = LeadListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [django_filters.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = LeadFilter
    search_fields = ['first_name', 'last_name', 'email', 'phone', 'notes_text']
    ordering_fields = ['created_at', 'status', 'assigned_at']
    ordering = ['-created_at']

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        logger.info(f"Fetching leads for user_id: {user_id}")
        logger.info(f"Requesting user: {self.request.user.id}, role: {self.request.user.role}")
        
        # First check if the target user exists
        try:
            target_user = CustomUser.objects.get(id=user_id)
            logger.info(f"Target user found: {target_user.email}, role: {target_user.role}")
        except CustomUser.DoesNotExist:
            logger.error(f"User with ID {user_id} does not exist")
            raise NotFound(detail=f"User with ID {user_id} does not exist")
        
        # Base queryset
        base_queryset = Lead.objects.all()
        logger.info(f"Base queryset count: {base_queryset.count()}")
        
        # If user is admin, they can view any spotter's leads
        if self.request.user.role == 'Admin':
            logger.info("Admin user accessing leads")
            queryset = base_queryset.filter(spotter_id=user_id)
            logger.info(f"Admin filtered queryset count: {queryset.count()}")
            return queryset
        
        # Regular users can only view their own leads
        if str(self.request.user.id) != user_id:
            logger.warning(f"User {self.request.user.id} attempted to access leads for user {user_id}")
            raise NotFound(detail="You don't have permission to view these leads")
            
        logger.info(f"User {self.request.user.id} accessing their own leads")
        queryset = base_queryset.filter(spotter=self.request.user)
        logger.info(f"User filtered queryset count: {queryset.count()}")
        return queryset

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
                'message': 'Leads retrieved successfully'
            })
        except NotFound as e:
            return Response({
                'status': 'error',
                'message': str(e.detail)
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error fetching leads: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'An error occurred while fetching leads'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 