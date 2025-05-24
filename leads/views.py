from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Lead, LeadImage
from .serializers import (
    LeadSubmissionSerializer, 
    LeadListSerializer, 
    AgencyLeadsSerializer, 
    LeadAssignmentSerializer,
    LeadDetailSerializer
)
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
        logger.info(f"Checking IsAgencyMember permission for user: {request.user.id}")
        logger.info(f"User role: {request.user.role}")
        logger.info(f"User agency: {request.user.agency}")
        
        has_permission = request.user and request.user.is_authenticated and (
            request.user.role == 'Admin' or 
            (request.user.role in ['Agent', 'Agency_Admin'] and request.user.agency is not None)
        )
        
        logger.info(f"Permission granted: {has_permission}")
        return has_permission

class LeadFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Lead.STATUS_CHOICES)
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    assigned = django_filters.BooleanFilter(field_name='agent', lookup_expr='isnull', exclude=True)

    class Meta:
        model = Lead
        fields = ['status', 'created_after', 'created_before', 'assigned']

class LeadListView(generics.ListAPIView):
    """
    View for listing all leads
    """
    serializer_class = LeadListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [django_filters.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = LeadFilter
    search_fields = ['first_name', 'last_name', 'email', 'phone', 'notes_text']
    ordering_fields = ['created_at', 'status', 'assigned_at']
    ordering = ['-created_at']

    def get_queryset(self):
        logger.info(f"Fetching leads for user: {self.request.user.id}, role: {self.request.user.role}")
        
        # Base queryset
        base_queryset = Lead.objects.all()
        logger.info(f"Base queryset count: {base_queryset.count()}")
        
        # If user is admin, they can view all leads
        if self.request.user.role == 'Admin':
            logger.info("Admin user accessing all leads")
            return base_queryset
        
        # If user is a spotter, they can only view their own leads
        if self.request.user.role == 'Spotter':
            logger.info(f"Spotter {self.request.user.id} accessing their leads")
            return base_queryset.filter(spotter=self.request.user)
        
        # If user is an agent or agency admin, they can view their agency's leads
        if self.request.user.role in ['Agent', 'Agency_Admin'] and self.request.user.agency:
            logger.info(f"Agency member {self.request.user.id} accessing their agency's leads")
            return base_queryset.filter(assigned_agency=self.request.user.agency)
        
        # Default to empty queryset for other roles
        logger.warning(f"User {self.request.user.id} with role {self.request.user.role} has no permission to view leads")
        return Lead.objects.none()

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
        except Exception as e:
            logger.error(f"Error fetching leads: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'An error occurred while fetching leads'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

class LeadAssignmentView(generics.UpdateAPIView):
    """
    View for assigning or reassigning a lead to an agent
    """
    serializer_class = LeadAssignmentSerializer
    permission_classes = [IsAuthenticated, IsAgencyMember]
    queryset = Lead.objects.all()
    lookup_field = 'id'

    def get_object(self):
        lead_id = self.kwargs.get('id')
        logger.info(f"=== Lead Assignment Request ===")
        logger.info(f"Lead ID from URL: {lead_id}")
        try:
            lead = Lead.objects.get(id=lead_id)
            logger.info(f"Found lead: {lead.id}")
            logger.info(f"Current lead state - Agent: {lead.agent}, Agency: {lead.assigned_agency}")
            return lead
        except Lead.DoesNotExist:
            logger.error(f"Lead with ID {lead_id} not found")
            raise NotFound(detail=f"Lead with ID {lead_id} not found")

    def update(self, request, *args, **kwargs):
        logger.info(f"=== Processing Lead Assignment ===")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request headers: {dict(request.headers)}")
        logger.info(f"Raw request data: {request.data}")
        logger.info(f"Request user: {request.user.id} ({request.user.email}), role: {request.user.role}")
        
        lead = self.get_object()
        logger.info(f"Processing assignment for lead {lead.id}")
        logger.info(f"Current lead state - Agent: {lead.agent}, Agency: {lead.assigned_agency}")

        # Check if user has permission to assign this lead
        if request.user.role == 'Admin':
            logger.info("Admin user assigning lead")
        elif str(request.user.agency_id) != str(lead.assigned_agency_id):
            logger.warning(f"User {request.user.id} attempted to assign lead {lead.id} from different agency")
            logger.warning(f"User's agency: {request.user.agency_id}, Lead's agency: {lead.assigned_agency_id}")
            raise PermissionDenied(detail="You don't have permission to assign this lead")

        # Validate the assignment data
        logger.info("Validating assignment data...")
        serializer = self.get_serializer(data=request.data, context={'lead': lead})
        if not serializer.is_valid():
            logger.error(f"Validation errors: {serializer.errors}")
            raise serializers.ValidationError(serializer.errors)
        logger.info(f"Validated data: {serializer.validated_data}")

        # Get the agent
        agent = CustomUser.objects.get(id=serializer.validated_data['agent_id'])
        logger.info(f"Found agent: {agent.id} ({agent.email}), role: {agent.role}, agency: {agent.agency_id}")

        # Update the lead
        try:
            logger.info("Updating lead...")
            lead.agent = agent
            if serializer.validated_data.get('notes'):
                lead.notes_text = serializer.validated_data['notes']
            lead.save()
            logger.info(f"Successfully updated lead {lead.id}")
            
            # Verify the update
            lead.refresh_from_db()
            logger.info(f"Lead after update - Agent: {lead.agent}, Agency: {lead.assigned_agency}")
        except Exception as e:
            logger.error(f"Error updating lead: {str(e)}")
            raise

        # Return the updated lead
        lead_serializer = LeadDetailSerializer(lead)
        logger.info("=== Lead Assignment Complete ===")
        return Response({
            'status': 'success',
            'message': 'Lead assigned successfully',
            'lead': lead_serializer.data
        })

class LeadDetailView(generics.RetrieveAPIView):
    """
    View for retrieving detailed information about a specific lead
    """
    serializer_class = LeadDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_object(self):
        lead_id = self.kwargs.get('id')
        try:
            lead = Lead.objects.get(id=lead_id)
            logger.info(f"Found lead: {lead.id}")
            
            # Check permissions
            if self.request.user.role == 'Admin':
                logger.info("Admin user accessing lead details")
                return lead
                
            if self.request.user.role == 'Spotter':
                if lead.spotter_id != self.request.user.id:
                    logger.warning(f"Spotter {self.request.user.id} attempted to access lead {lead.id} from different spotter")
                    raise PermissionDenied(detail="You don't have permission to view this lead")
                logger.info(f"Spotter {self.request.user.id} accessing their lead")
                return lead
                
            if self.request.user.role in ['Agent', 'Agency_Admin']:
                if str(lead.assigned_agency_id) != str(self.request.user.agency_id):
                    logger.warning(f"Agency member {self.request.user.id} attempted to access lead {lead.id} from different agency")
                    raise PermissionDenied(detail="You don't have permission to view this lead")
                logger.info(f"Agency member {self.request.user.id} accessing their agency's lead")
                return lead
                
            logger.warning(f"User {self.request.user.id} with role {self.request.user.role} has no permission to view lead")
            raise PermissionDenied(detail="You don't have permission to view this lead")
            
        except Lead.DoesNotExist:
            logger.error(f"Lead with ID {lead_id} not found")
            raise NotFound(detail=f"Lead with ID {lead_id} not found")

    def retrieve(self, request, *args, **kwargs):
        try:
            lead = self.get_object()
            serializer = self.get_serializer(lead)
            return Response({
                'status': 'success',
                'lead': serializer.data,
                'message': 'Lead details retrieved successfully'
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
            logger.error(f"Error fetching lead details: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'An error occurred while fetching lead details'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)