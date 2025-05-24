from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Lead, LeadImage
from .serializers import LeadSubmissionSerializer, LeadListSerializer, AgencyLeadsSerializer
from rest_framework.permissions import BasePermission
from django_filters import rest_framework as django_filters
from rest_framework.exceptions import NotFound, PermissionDenied
from users.models import CustomUser, Agency
import logging

logger = logging.getLogger(__name__)

class IsSpotter(BasePermission):
    """
    Custom permission to only allow spotters to submit leads
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'Spotter'

class IsAgencyMember(BasePermission):
    """
    Custom permission to only allow agency members to access agency leads
    """
    def has_permission(self, request, view):
        logger.info("=== IsAgencyMember Permission Check ===")
        logger.info(f"User ID: {request.user.id}")
        logger.info(f"User Email: {request.user.email}")
        logger.info(f"User Role: {request.user.role}")
        logger.info(f"User Agency ID: {request.user.agency_id}")
        logger.info(f"User Agency: {request.user.agency}")
        logger.info(f"Is Authenticated: {request.user.is_authenticated}")
        
        has_permission = request.user and request.user.is_authenticated and (
            request.user.role == 'Admin' or 
            (request.user.role in ['Agent', 'Agency_Admin'] and request.user.agency is not None)
        )
        
        logger.info(f"Permission Check Result: {has_permission}")
        logger.info("=== End Permission Check ===")
        return has_permission

class LeadFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Lead.STATUS_CHOICES)
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    assigned = django_filters.BooleanFilter(field_name='agent', lookup_expr='isnull', exclude=True)

    class Meta:
        model = Lead
        fields = ['status', 'created_after', 'created_before', 'assigned']

class AgencyLeadsListView(generics.ListAPIView):
    serializer_class = AgencyLeadsSerializer
    permission_classes = [IsAuthenticated, IsAgencyMember]
    filter_backends = [django_filters.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = LeadFilter
    search_fields = ['first_name', 'last_name', 'email', 'phone', 'notes_text']
    ordering_fields = ['created_at', 'status', 'assigned_at']
    ordering = ['-created_at']

    def get_queryset(self):
        logger.info("=== AgencyLeadsListView.get_queryset ===")
        agency_id = self.kwargs.get('agency_id')
        logger.info(f"Requested Agency ID: {agency_id}")
        logger.info(f"Requesting User ID: {self.request.user.id}")
        logger.info(f"Requesting User Role: {self.request.user.role}")
        logger.info(f"Requesting User Agency ID: {self.request.user.agency_id}")
        
        # First check if the agency exists
        try:
            agency = Agency.objects.get(id=agency_id)
            logger.info(f"Agency found: {agency.name}")
        except Agency.DoesNotExist:
            logger.error(f"Agency with ID {agency_id} does not exist")
            raise NotFound(detail=f"Agency with ID {agency_id} does not exist")
        
        # Base queryset
        base_queryset = Lead.objects.all()
        logger.info(f"Base queryset count: {base_queryset.count()}")
        
        # If user is system admin, they can view any agency's leads
        if self.request.user.role == 'Admin':
            logger.info("Admin user accessing agency leads")
            queryset = base_queryset.filter(assigned_agency_id=agency_id)
            logger.info(f"Admin filtered queryset count: {queryset.count()}")
            return queryset
        
        # Agency members can only view their own agency's leads
        if str(self.request.user.agency_id) != str(agency_id):
            logger.warning(f"User {self.request.user.id} attempted to access leads for agency {agency_id}")
            logger.warning(f"User's agency ID: {self.request.user.agency_id}")
            logger.warning(f"Requested agency ID: {agency_id}")
            raise PermissionDenied(detail="You don't have permission to view these leads")
            
        logger.info(f"User {self.request.user.id} accessing their agency's leads")
        queryset = base_queryset.filter(assigned_agency_id=agency_id)
        logger.info(f"Agency filtered queryset count: {queryset.count()}")
        logger.info("=== End get_queryset ===")
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
                'results': serializer.data,
                'message': 'Agency leads retrieved successfully'
            })
        except NotFound as e:
            return Response({
                'status': 'error',
                'message': str(e.detail)
            }, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({
                'status': 'error',
                'message': str(e.detail)
            }, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.error(f"Error fetching agency leads: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'An error occurred while fetching agency leads'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LeadSubmissionView(generics.CreateAPIView):
    serializer_class = LeadSubmissionSerializer
    permission_classes = [IsAuthenticated, IsSpotter]

    def create(self, request, *args, **kwargs):
        logger.info(f"Received lead submission data: {request.data}")
        logger.info(f"Files: {request.FILES}")
        
        # Extract basic lead data
        lead_data = {
            'first_name': request.data.get('first_name'),
            'last_name': request.data.get('last_name'),
            'email': request.data.get('email'),
            'phone': request.data.get('phone'),
            'notes_text': request.data.get('notes_text', ''),
        }
        
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'email', 'phone']
        missing_fields = [field for field in required_fields if not lead_data.get(field)]
        
        if missing_fields:
            return Response({
                'status': 'error',
                'message': f'Missing required fields: {", ".join(missing_fields)}',
                'missing_fields': missing_fields
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Create the lead
            lead = Lead.objects.create(
                spotter=request.user,
                **lead_data
            )
            
            # Handle images
            image_count = int(request.data.get('image_count', 0))
            created_images = []
            
            for i in range(image_count):
                image_key = f'image_{i}'
                description_key = f'description_{i}'
                
                if image_key in request.FILES:
                    image_file = request.FILES[image_key]
                    description = request.data.get(description_key, '')
                    
                    lead_image = LeadImage.objects.create(
                        lead=lead,
                        image=image_file,
                        description=description
                    )
                    created_images.append({
                        'id': lead_image.id,
                        'image': lead_image.image.url,
                        'description': lead_image.description
                    })
            
            # Return success response
            response_data = {
                'status': 'success',
                'message': 'Lead submitted successfully',
                'data': {
                    'id': lead.id,
                    'first_name': lead.first_name,
                    'last_name': lead.last_name,
                    'email': lead.email,
                    'phone': lead.phone,
                    'notes_text': lead.notes_text,
                    'status': lead.status,
                    'images': created_images,
                    'created_at': lead.created_at.isoformat()
                }
            }
            
            logger.info(f"Lead created successfully: {lead.id}")
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating lead: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'An error occurred while creating the lead',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
                'results': serializer.data,
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