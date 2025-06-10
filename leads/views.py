from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Lead, LeadImage
from properties.models import Property
from .serializers import (
    LeadSubmissionSerializer, 
    LeadListSerializer, 
    AgencyLeadsSerializer, 
    LeadAssignmentSerializer,
    LeadDetailSerializer,
    LeadAcceptanceSerializer,
    LeadPropertyUpdateSerializer,
    LeadWhatsAppNotificationSerializer,
    LeadCompletionSerializer,
    LeadFailureSerializer
)
from rest_framework.permissions import BasePermission
from django_filters import rest_framework as django_filters
from rest_framework.exceptions import NotFound, PermissionDenied
from users.models import CustomUser, Agency
import logging
from updates.twilio_handler import send_message as send_whatsapp_message
from django.utils import timezone

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
    is_accepted = django_filters.BooleanFilter(field_name='is_accepted')

    class Meta:
        model = Lead
        fields = ['status', 'created_after', 'created_before', 'assigned', 'is_accepted']

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
    search_fields = ['first_name', 'last_name', 'email', 'phone', 'notes_text', 'street_address', 'suburb']
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
            'street_address': request.data.get('street_address'),
            'suburb': request.data.get('suburb'),
            'notes_text': request.data.get('notes_text', ''),
            'preferred_agent': request.data.get('preferred_agent', ''),
        }
        
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'phone', 'street_address', 'suburb']
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
            
            # Send WhatsApp notification to spotter
            if request.user.phone:
                try:
                    send_whatsapp_message(
                        phone_number=request.user.phone,
                        template_name='lead_submitted',
                        variables={
                            '1': f"{request.user.first_name} {request.user.last_name}"
                        }
                    )
                    logger.info(f"Sent WhatsApp notification to spotter {request.user.id}")
                except Exception as e:
                    logger.error(f"Failed to send WhatsApp notification: {str(e)}")
                    # Don't fail the lead submission if WhatsApp fails
            
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
                    'street_address': lead.street_address,
                    'suburb': lead.suburb,
                    'notes_text': lead.notes_text,
                    'preferred_agent': lead.preferred_agent,
                    'status': lead.status,
                    'images': created_images,
                    'created_at': lead.created_at.isoformat()
                }
            }
            # Send whatsapp message to +27798557301
            send_whatsapp_message(
                phone_number='+27798557301',
                template_name='notify_manager_spotter_create',
                variables={
                    '1': f"{request.user.first_name} {request.user.last_name}",
                    '2': f"{lead.street_address}",
                    '3': f"{lead.suburb}",
                    '4': f"{lead.preferred_agent}",
                }
            )
            logger.info(f"Sent WhatsApp notification to manager {request.user.id}")

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
    """
    View for listing all leads submitted by a specific spotter
    """
    serializer_class = LeadListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [django_filters.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = LeadFilter
    search_fields = ['first_name', 'last_name', 'email', 'phone', 'notes_text']
    ordering_fields = ['created_at', 'status', 'assigned_at']
    ordering = ['-created_at']

    def get_queryset(self):
        spotter_id = self.kwargs.get('spotter_id')
        logger.info(f"=== Fetching Leads for Spotter ===")
        logger.info(f"Requesting user: {self.request.user.id} ({self.request.user.email}), role: {self.request.user.role}")
        logger.info(f"Target spotter ID: {spotter_id}")

        try:
            # Get the spotter
            spotter = CustomUser.objects.get(id=spotter_id, role='Spotter')
            logger.info(f"Found spotter: {spotter.email}")

            # Check permissions
            if self.request.user.role == 'Admin':
                logger.info("Admin user accessing spotter leads")
                return Lead.objects.filter(spotter=spotter)

            # Spotters can only view their own leads
            if str(self.request.user.id) != str(spotter_id):
                logger.warning(f"User {self.request.user.id} attempted to access leads for spotter {spotter.id}")
                raise PermissionDenied(detail="You don't have permission to view these leads")

            logger.info(f"Spotter {spotter.id} accessing their own leads")
            return Lead.objects.filter(spotter=spotter)

        except CustomUser.DoesNotExist:
            logger.error(f"Spotter with ID {spotter_id} not found")
            raise NotFound(detail=f"Spotter with ID {spotter_id} not found")

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
                'message': 'Spotter leads retrieved successfully'
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
            logger.error(f"Error fetching spotter leads: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'An error occurred while fetching spotter leads'
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

            # Send WhatsApp notification to spotter
            if lead.spotter and lead.spotter.phone:
                try:
                    send_whatsapp_message(
                        phone_number=lead.spotter.phone,
                        template_name='lead_assigned',
                        variables={
                            '1': f"{lead.spotter.first_name} {lead.spotter.last_name}",
                            '2': f"{agent.first_name} {agent.last_name}"
                        }
                    )
                    logger.info(f"Sent WhatsApp notification to spotter {lead.spotter.id}")

                    # Send whatsapp message to agent
                    send_whatsapp_message(
                        phone_number='+27798557301',
                        template_name='notify_agent_lead_assigned',
                        variables={
                            '1': f"{agent.first_name}",
                            '2': f"{agent.last_name}"
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to send WhatsApp notification: {str(e)}")
                    # Don't fail the assignment if WhatsApp fails
            # Send whatsapp message to +27798557301

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

class AgentLeadsView(generics.ListAPIView):
    """
    View for listing all leads assigned to a specific agent
    """
    serializer_class = AgencyLeadsSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [django_filters.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = LeadFilter
    search_fields = ['first_name', 'last_name', 'email', 'phone', 'notes_text']
    ordering_fields = ['created_at', 'status', 'assigned_at', 'accepted_at']
    ordering = ['-created_at']

    def get_queryset(self):
        agent_id = self.kwargs.get('agent_id')
        logger.info(f"=== Fetching Leads for Agent ===")
        logger.info(f"Requesting user: {self.request.user.id} ({self.request.user.email}), role: {self.request.user.role}")
        logger.info(f"Target agent ID: {agent_id}")

        try:
            # Get the agent
            agent = CustomUser.objects.get(id=agent_id)
            logger.info(f"Found agent: {agent.email}, agency: {agent.agency_id}")

            # Check permissions
            if self.request.user.role == 'Admin':
                logger.info("Admin user accessing agent leads")
                return Lead.objects.filter(agent=agent)

            # Agency members can only view leads from their own agency
            if str(self.request.user.agency_id) != str(agent.agency_id):
                logger.warning(f"User {self.request.user.id} attempted to access leads for agent {agent.id} from different agency")
                raise PermissionDenied(detail="You don't have permission to view these leads")

            # If the requesting user is the agent themselves, they can view their leads
            if self.request.user.id == agent.id:
                logger.info(f"Agent {agent.id} accessing their own leads")
                # By default, only show accepted leads for the agent themselves
                show_all = self.request.query_params.get('show_all', 'false').lower() == 'true'
                queryset = Lead.objects.filter(agent=agent)
                if not show_all:
                    queryset = queryset.filter(is_accepted=True)
                return queryset

            # Agency admins can view leads of agents in their agency
            if self.request.user.role == 'Agency_Admin' and agent.role == 'Agent':
                logger.info(f"Agency admin {self.request.user.id} accessing leads for agent {agent.id}")
                return Lead.objects.filter(agent=agent)

            logger.warning(f"User {self.request.user.id} has no permission to view leads for agent {agent.id}")
            raise PermissionDenied(detail="You don't have permission to view these leads")

        except CustomUser.DoesNotExist:
            logger.error(f"Agent with ID {agent_id} not found")
            raise NotFound(detail=f"Agent with ID {agent_id} not found")

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
                'message': 'Agent leads retrieved successfully'
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
            logger.error(f"Error fetching agent leads: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'An error occurred while fetching agent leads'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LeadAcceptanceView(generics.UpdateAPIView):
    """
    View for accepting or rejecting a lead
    """
    serializer_class = LeadAcceptanceSerializer
    permission_classes = [IsAuthenticated]
    queryset = Lead.objects.all()
    lookup_field = 'id'

    def get_object(self):
        lead_id = self.kwargs.get('id')
        logger.info(f"=== Lead Acceptance Request ===")
        logger.info(f"Lead ID: {lead_id}")
        logger.info(f"Requesting user: {self.request.user.id} ({self.request.user.email}), role: {self.request.user.role}")
        
        try:
            lead = Lead.objects.get(id=lead_id)
            logger.info(f"Found lead: {lead.id}")
            
            # Check permissions
            if self.request.user.role == 'Admin':
                logger.info("Admin user accessing lead")
                return lead
                
            if lead.agent_id != self.request.user.id:
                logger.warning(f"User {self.request.user.id} attempted to accept/reject lead {lead.id} assigned to different agent")
                raise PermissionDenied(detail="You can only accept/reject leads assigned to you")
                
            return lead
            
        except Lead.DoesNotExist:
            logger.error(f"Lead with ID {lead_id} not found")
            raise NotFound(detail=f"Lead with ID {lead_id} not found")

    def update(self, request, *args, **kwargs):
        lead = self.get_object()
        logger.info(f"Processing {request.data.get('action')} for lead {lead.id}")
        
        serializer = self.get_serializer(data=request.data, context={'lead': lead})
        serializer.is_valid(raise_exception=True)
        
        action = serializer.validated_data['action']
        notes = serializer.validated_data.get('notes', '')
        
        try:
            if action == 'accept':
                # Create a new property with placeholder data
                property_data = {
                    'title': f"Property for {lead.first_name} {lead.last_name}",
                    'description': f"Property created from lead {lead.id}. {notes}",
                    'property_type': 'residential',  # Default type
                    'status': 'available',
                    'price': 0,  # Placeholder price
                    'address': 'To be filled by agent',
                    'city': 'To be filled by agent',
                    'state': 'To be filled by agent',
                    'zip_code': '0000',
                    'owner': request.user
                }
                
                property = Property.objects.create(**property_data)
                logger.info(f"Created new property {property.id} for lead {lead.id}")
                
                # Update the lead
                lead.property = property
                lead.accept_lead()
                if notes:
                    lead.notes_text = notes
                lead.save()
                
                logger.info(f"Lead {lead.id} accepted and linked to property {property.id}")
                
            else:  # reject
                lead.reject_lead()
                if notes:
                    lead.notes_text = notes
                lead.save()
                logger.info(f"Lead {lead.id} rejected")
            
            # Return the updated lead
            lead_serializer = LeadDetailSerializer(lead)
            return Response({
                'status': 'success',
                'message': f'Lead {action}ed successfully',
                'lead': lead_serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error processing lead {action}: {str(e)}")
            return Response({
                'status': 'error',
                'message': f'An error occurred while {action}ing the lead'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LeadPropertyUpdateView(generics.UpdateAPIView):
    """
    View for updating property details of a lead
    """
    serializer_class = LeadPropertyUpdateSerializer
    permission_classes = [IsAuthenticated]
    queryset = Lead.objects.all()
    lookup_field = 'id'

    def get_object(self):
        lead_id = self.kwargs.get('id')
        logger.info(f"=== Lead Property Update Request ===")
        logger.info(f"Lead ID: {lead_id}")
        logger.info(f"Requesting user: {self.request.user.id} ({self.request.user.email}), role: {self.request.user.role}")
        
        try:
            lead = Lead.objects.get(id=lead_id)
            logger.info(f"Found lead: {lead.id}")
            
            # Check permissions
            if self.request.user.role == 'Admin':
                logger.info("Admin user accessing lead")
                return lead
                
            if lead.agent_id != self.request.user.id:
                logger.warning(f"User {self.request.user.id} attempted to update lead {lead.id} assigned to different agent")
                raise PermissionDenied(detail="You can only update leads assigned to you")
                
            return lead
            
        except Lead.DoesNotExist:
            logger.error(f"Lead with ID {lead_id} not found")
            raise NotFound(detail=f"Lead with ID {lead_id} not found")

    def update(self, request, *args, **kwargs):
        lead = self.get_object()
        logger.info(f"Processing property update for lead {lead.id}")
        logger.info(f"Request data: {request.data}")
        logger.info(f"Request content type: {request.content_type}")
        
        serializer = self.get_serializer(data=request.data, context={'lead': lead})
        if not serializer.is_valid():
            logger.error(f"Validation errors: {serializer.errors}")
            return Response({
                'status': 'error',
                'message': 'Validation error',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            updated_lead = serializer.update(lead, serializer.validated_data)
            lead_serializer = LeadDetailSerializer(updated_lead)
            
            logger.info(f"Successfully updated property for lead {lead.id}")
            return Response({
                'status': 'success',
                'message': 'Property details updated successfully',
                'lead': lead_serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error updating property for lead {lead.id}: {str(e)}")
            return Response({
                'status': 'error',
                'message': f'An error occurred while updating the property',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LeadWhatsAppNotificationView(generics.CreateAPIView):
    """
    View for sending WhatsApp notifications about lead updates
    """
    serializer_class = LeadWhatsAppNotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'message': 'Validation error',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            template_name = serializer.validated_data['template_name']
            variables = serializer.validated_data['variables']
            
            # Get the lead from the URL parameter
            lead_id = self.kwargs.get('id')
            try:
                lead = Lead.objects.get(id=lead_id)
            except Lead.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': f'Lead with ID {lead_id} not found'
                }, status=status.HTTP_404_NOT_FOUND)
                
            # Get spotter's phone number
            if not lead.spotter or not lead.spotter.phone:
                return Response({
                    'status': 'error',
                    'message': 'Lead has no spotter or spotter has no phone number'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            # Send WhatsApp message
            success = send_whatsapp_message(
                phone_number=lead.spotter.phone,
                template_name=template_name,
                variables=variables
            )
            
            if success:
                return Response({
                    'status': 'success',
                    'message': 'WhatsApp notification sent successfully'
                })
            else:
                return Response({
                    'status': 'error',
                    'message': 'Failed to send WhatsApp notification'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Error sending WhatsApp notification: {str(e)}")
            return Response({
                'status': 'error',
                'message': f'An error occurred while sending the notification: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LeadCompletionView(generics.UpdateAPIView):
    """
    View for marking a lead as complete (property sold)
    """
    serializer_class = LeadCompletionSerializer
    permission_classes = [IsAuthenticated]
    queryset = Lead.objects.all()
    lookup_field = 'id'

    def get_object(self):
        lead_id = self.kwargs.get('id')
        logger.info(f"=== Lead Completion Request ===")
        logger.info(f"Lead ID: {lead_id}")
        logger.info(f"Requesting user: {self.request.user.id} ({self.request.user.email}), role: {self.request.user.role}")
        
        try:
            lead = Lead.objects.get(id=lead_id)
            logger.info(f"Found lead: {lead.id}")
            
            # Check permissions
            if self.request.user.role == 'Admin':
                logger.info("Admin user accessing lead")
                return lead
                
            if lead.agent_id != self.request.user.id:
                logger.warning(f"User {self.request.user.id} attempted to complete lead {lead.id} assigned to different agent")
                raise PermissionDenied(detail="You can only complete leads assigned to you")
                
            return lead
            
        except Lead.DoesNotExist:
            logger.error(f"Lead with ID {lead_id} not found")
            raise NotFound(detail=f"Lead with ID {lead_id} not found")

    def update(self, request, *args, **kwargs):
        lead = self.get_object()
        logger.info(f"Processing completion for lead {lead.id}")
        
        serializer = self.get_serializer(data=request.data, context={'lead': lead})
        if not serializer.is_valid():
            logger.error(f"Validation errors: {serializer.errors}")
            return Response({
                'status': 'error',
                'message': 'Validation error',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Update property status to sold
            lead.property.status = 'sold'
            lead.property.price = serializer.validated_data['final_price']
            lead.property.save()
            
            # Update lead status to closed
            lead.status = 'closed'
            lead.closed_at = timezone.now()
            if serializer.validated_data.get('notes'):
                lead.notes_text = serializer.validated_data['notes']
            lead.save()
            
            # Send WhatsApp notification to spotter
            if lead.spotter and lead.spotter.phone:
                send_whatsapp_message(
                    phone_number=lead.spotter.phone,
                    template_name='sale_complete',
                    variables={
                        '1': f"{lead.first_name} {lead.last_name}",
                        '2': str(serializer.validated_data['final_price'])
                    }
                )
            
            lead_serializer = LeadDetailSerializer(lead)
            return Response({
                'status': 'success',
                'message': 'Lead marked as complete successfully',
                'lead': lead_serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error completing lead {lead.id}: {str(e)}")
            return Response({
                'status': 'error',
                'message': f'An error occurred while completing the lead: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LeadFailureView(generics.UpdateAPIView):
    """
    View for marking a lead as failed
    """
    serializer_class = LeadFailureSerializer
    permission_classes = [IsAuthenticated]
    queryset = Lead.objects.all()
    lookup_field = 'id'

    def get_object(self):
        lead_id = self.kwargs.get('id')
        logger.info(f"=== Lead Failure Request ===")
        logger.info(f"Lead ID: {lead_id}")
        logger.info(f"Requesting user: {self.request.user.id} ({self.request.user.email}), role: {self.request.user.role}")
        
        try:
            lead = Lead.objects.get(id=lead_id)
            logger.info(f"Found lead: {lead.id}")
            
            # Check permissions
            if self.request.user.role == 'Admin':
                logger.info("Admin user accessing lead")
                return lead
                
            if lead.agent_id != self.request.user.id:
                logger.warning(f"User {self.request.user.id} attempted to mark lead {lead.id} as failed")
                raise PermissionDenied(detail="You can only mark leads assigned to you as failed")
                
            return lead
            
        except Lead.DoesNotExist:
            logger.error(f"Lead with ID {lead_id} not found")
            raise NotFound(detail=f"Lead with ID {lead_id} not found")

    def update(self, request, *args, **kwargs):
        lead = self.get_object()
        logger.info(f"Processing failure for lead {lead.id}")
        
        serializer = self.get_serializer(data=request.data, context={'lead': lead})
        if not serializer.is_valid():
            logger.error(f"Validation errors: {serializer.errors}")
            return Response({
                'status': 'error',
                'message': 'Validation error',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Update lead status to closed
            lead.status = 'closed'
            lead.closed_at = timezone.now()
            
            # Add failure reason and notes to lead notes
            failure_note = f"Lead marked as failed. Reason: {serializer.validated_data['reason']}"
            if serializer.validated_data.get('notes'):
                failure_note += f"\nAdditional notes: {serializer.validated_data['notes']}"
            
            lead.notes_text = failure_note
            lead.save()
            
            # Send WhatsApp notification to spotter
            if lead.spotter and lead.spotter.phone:
                send_whatsapp_message(
                    phone_number=lead.spotter.phone,
                    template_name='lead_failed',
                    variables={
                        '1': f"{lead.first_name} {lead.last_name}",
                        '2': serializer.validated_data['reason']
                    }
                )
            
            lead_serializer = LeadDetailSerializer(lead)
            return Response({
                'status': 'success',
                'message': 'Lead marked as failed successfully',
                'lead': lead_serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error marking lead {lead.id} as failed: {str(e)}")
            return Response({
                'status': 'error',
                'message': f'An error occurred while marking the lead as failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)