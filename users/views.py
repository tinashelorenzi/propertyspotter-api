from django.shortcuts import render
from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .serializers import (
    UserRegistrationSerializer, 
    EmailVerificationSerializer, 
    AgencySerializer, 
    EmailAuthTokenSerializer,
    UserDetailSerializer,
    UserProfileUpdateSerializer,
    AgencyAgentsSerializer,
    AgentInvitationSerializer,
    PasswordSetSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer
)
from .models import VerificationToken, Agency, CustomUser, InvitationToken
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from django.shortcuts import get_object_or_404
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied, NotFound
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)

User = get_user_model()

class IsAgencyMember(BasePermission):
    """
    Custom permission to only allow agency members to access agency information
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.role == 'Admin' or 
            (request.user.role in ['Agent', 'Agency_Admin'] and request.user.agency is not None)
        )

class AgencyAgentsListView(generics.ListAPIView):
    serializer_class = AgencyAgentsSerializer
    permission_classes = [IsAuthenticated, IsAgencyMember]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['email', 'username', 'first_name', 'last_name', 'phone']
    ordering_fields = ['created_at', 'last_login', 'first_name', 'last_name']
    ordering = ['-created_at']

    def get_queryset(self):
        agency_id = self.kwargs.get('agency_id')
        logger.info(f"Fetching agents for agency_id: {agency_id}")
        logger.info(f"Requesting user: {self.request.user.id}, role: {self.request.user.role}")
        
        # First check if the agency exists
        try:
            agency = Agency.objects.get(id=agency_id)
            logger.info(f"Agency found: {agency.name}")
        except Agency.DoesNotExist:
            logger.error(f"Agency with ID {agency_id} does not exist")
            raise NotFound(detail=f"Agency with ID {agency_id} does not exist")
        
        # Base queryset - get all agents in the agency
        base_queryset = CustomUser.objects.filter(
            agency_id=agency_id,
            role__in=['Agent', 'Agency_Admin']  # Only get agents and agency admins
        )
        logger.info(f"Base queryset count: {base_queryset.count()}")
        
        # If user is system admin, they can view any agency's agents
        if self.request.user.role == 'Admin':
            logger.info("Admin user accessing agency agents")
            return base_queryset
        
        # Agency members can only view their own agency's agents
        if str(self.request.user.agency_id) != str(agency_id):
            logger.warning(f"User {self.request.user.id} attempted to access agents for agency {agency_id}")
            raise PermissionDenied(detail="You don't have permission to view these agents")
            
        logger.info(f"User {self.request.user.id} accessing their agency's agents")
        return base_queryset

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
                'message': 'Agency agents retrieved successfully'
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
            logger.error(f"Error fetching agency agents: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'An error occurred while fetching agency agents'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AgencyListView(generics.ListAPIView):
    """
    View to list all agencies
    """
    queryset = Agency.objects.all()
    serializer_class = AgencySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'email', 'phone', 'address']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

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
                'message': 'Agencies retrieved successfully'
            })
        except Exception as e:
            logger.error(f"Error fetching agencies: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'An error occurred while fetching agencies'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Create your views here.

class AgencyCreateView(generics.CreateAPIView):
    queryset = Agency.objects.all()
    serializer_class = AgencySerializer
    permission_classes = [AllowAny]

class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        # Create verification token
        token = VerificationToken.objects.create(user=user)
        # Send verification email
        self.send_verification_email(user, token)

    def send_verification_email(self, user, token):
        # This will be implemented when we set up email configuration
        pass

class EmailVerificationView(generics.GenericAPIView):
    serializer_class = EmailVerificationSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = VerificationToken.objects.get(token=serializer.validated_data['token'])
        user = token.user
        
        # Activate the user
        user.is_active = True
        user.save()
        
        # Mark token as used
        token.used = True
        token.save()
        
        return Response(
            {
                'message': 'Email verified successfully',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                    'is_active': user.is_active
                }
            },
            status=status.HTTP_200_OK
        )

class EmailLoginView(generics.CreateAPIView):
    serializer_class = EmailAuthTokenSerializer
    permission_classes = [AllowAny]
    authentication_classes = [TokenAuthentication]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        # Create or get token
        token, created = Token.objects.get_or_create(user=user)
        
        # Prepare agency information
        agency_info = None
        if user.agency:
            agency_info = {
                'id': user.agency.id,
                'name': user.agency.name,
                'email': user.agency.email,
                'phone': user.agency.phone,
                'address': user.agency.address,
                'license_valid_until': user.agency.license_valid_until
            }
        
        return Response({
            'token': token.key,
            'user': {
                'id': user.pk,
                'email': user.email,
                'username': user.username,
                'role': user.role,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_active': user.is_active,
                'agency': agency_info
            }
        })

class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'

    def get_object(self):
        obj = get_object_or_404(self.get_queryset(), id=self.kwargs["id"])
        return obj

class UserProfileView(generics.RetrieveAPIView):
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

class UserProfileUpdateView(generics.UpdateAPIView):
    serializer_class = UserProfileUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

class AgentInvitationView(generics.CreateAPIView):
    """
    View for inviting an agent to join an agency
    """
    serializer_class = AgentInvitationSerializer
    permission_classes = [IsAuthenticated, IsAgencyMember]

    def create(self, request, *args, **kwargs):
        logger.info(f"Processing agent invitation request from user {request.user.id}")
        logger.info(f"Request data: {request.data}")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create invitation token
        invitation = InvitationToken.objects.create(
            email=serializer.validated_data['email'],
            first_name=serializer.validated_data['first_name'],
            last_name=serializer.validated_data['last_name'],
            phone=serializer.validated_data['phone'],
            agency=request.user.agency,
            expires_at=timezone.now() + timedelta(days=7)  # Token expires in 7 days
        )

        # Send invitation email
        try:
            frontend_url = settings.FRONTEND_URL
            invitation_url = f"{frontend_url}/set-password/{invitation.token}"
            
            subject = "You've been invited to join Property Spotter"
            html_message = f"""
            <h2>Welcome to Property Spotter!</h2>
            <p>Hello {invitation.first_name},</p>
            <p>You've been invited to join {invitation.agency.name} on Property Spotter.</p>
            <p>Click the link below to set your password and complete your registration:</p>
            <p><a href="{invitation_url}">{invitation_url}</a></p>
            <p>This link will expire in 7 days.</p>
            <p>If you didn't expect this invitation, please ignore this email.</p>
            """
            
            send_mail(
                subject=subject,
                message=strip_tags(html_message),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[invitation.email],
                html_message=html_message
            )
            
            logger.info(f"Invitation email sent to {invitation.email}")
            
            return Response({
                'status': 'success',
                'message': 'Invitation sent successfully',
                'data': {
                    'email': invitation.email,
                    'expires_at': invitation.expires_at
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error sending invitation email: {str(e)}")
            invitation.delete()  # Clean up the invitation if email fails
            return Response({
                'status': 'error',
                'message': 'Failed to send invitation email'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SetPasswordView(generics.CreateAPIView):
    """
    View for setting password using invitation token
    """
    serializer_class = PasswordSetSerializer
    permission_classes = []  # No authentication required

    def create(self, request, *args, **kwargs):
        logger.info("Processing password set request")
        logger.info(f"Request data: {request.data}")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # Get and validate invitation token
            invitation = InvitationToken.objects.get(
                token=serializer.validated_data['token'],
                is_used=False
            )

            if invitation.is_expired():
                logger.warning(f"Expired token used: {invitation.token}")
                return Response({
                    'status': 'error',
                    'message': 'Invitation link has expired'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Generate username from first and last name
            base_username = f"{invitation.first_name.lower()}.{invitation.last_name.lower()}"
            username = base_username
            counter = 1
            
            # Ensure username is unique
            while CustomUser.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            # Create the user
            user = CustomUser.objects.create_user(
                username=username,
                email=invitation.email,
                password=serializer.validated_data['password'],
                first_name=invitation.first_name,
                last_name=invitation.last_name,
                phone=invitation.phone,
                agency=invitation.agency,
                role='Agent',
                is_active=True
            )

            # Mark invitation as used
            invitation.is_used = True
            invitation.save()

            logger.info(f"Successfully created user account for {user.email} with username {username}")

            return Response({
                'status': 'success',
                'message': 'Password set successfully. You can now log in.',
                'data': {
                    'email': user.email,
                    'username': username,
                    'name': f"{user.first_name} {user.last_name}"
                }
            }, status=status.HTTP_201_CREATED)

        except InvitationToken.DoesNotExist:
            logger.warning(f"Invalid token used: {serializer.validated_data['token']}")
            return Response({
                'status': 'error',
                'message': 'Invalid or expired invitation link'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error setting password: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'An error occurred while setting your password'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DeactivateUserView(generics.UpdateAPIView):
    """
    View for deactivating a user account
    """
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated, IsAgencyMember]
    queryset = CustomUser.objects.all()
    lookup_field = 'id'

    def get_object(self):
        user_id = self.kwargs.get('id')
        logger.info(f"=== User Deactivation Request ===")
        logger.info(f"Requesting user: {self.request.user.id} ({self.request.user.email}), role: {self.request.user.role}")
        logger.info(f"Target user ID: {user_id}")

        try:
            user = CustomUser.objects.get(id=user_id)
            logger.info(f"Found user: {user.email}, role: {user.role}, agency: {user.agency_id}")

            # Check permissions
            if self.request.user.role == 'Admin':
                logger.info("Admin user deactivating account")
                return user

            # Agency members can only deactivate users from their own agency
            if str(self.request.user.agency_id) != str(user.agency_id):
                logger.warning(f"User {self.request.user.id} attempted to deactivate user {user.id} from different agency")
                raise PermissionDenied(detail="You don't have permission to deactivate this user")

            # Agency admins can only deactivate agents
            if self.request.user.role == 'Agency_Admin' and user.role != 'Agent':
                logger.warning(f"Agency admin {self.request.user.id} attempted to deactivate non-agent user {user.id}")
                raise PermissionDenied(detail="You can only deactivate agent accounts")

            return user

        except CustomUser.DoesNotExist:
            logger.error(f"User with ID {user_id} not found")
            raise NotFound(detail=f"User with ID {user_id} not found")

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        logger.info(f"Deactivating user: {user.email}")

        try:
            user.is_active = False
            user.save()
            logger.info(f"Successfully deactivated user {user.id}")

            return Response({
                'status': 'success',
                'message': 'User account deactivated successfully',
                'data': {
                    'id': user.id,
                    'email': user.email,
                    'name': f"{user.first_name} {user.last_name}",
                    'is_active': user.is_active
                }
            })

        except Exception as e:
            logger.error(f"Error deactivating user: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'An error occurred while deactivating the user account'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ReactivateUserView(generics.UpdateAPIView):
    """
    View for reactivating a user account
    """
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated, IsAgencyMember]
    queryset = CustomUser.objects.all()
    lookup_field = 'id'

    def get_object(self):
        user_id = self.kwargs.get('id')
        logger.info(f"=== User Reactivation Request ===")
        logger.info(f"Requesting user: {self.request.user.id} ({self.request.user.email}), role: {self.request.user.role}")
        logger.info(f"Target user ID: {user_id}")

        try:
            user = CustomUser.objects.get(id=user_id)
            logger.info(f"Found user: {user.email}, role: {user.role}, agency: {user.agency_id}")

            # Check permissions
            if self.request.user.role == 'Admin':
                logger.info("Admin user reactivating account")
                return user

            # Agency members can only reactivate users from their own agency
            if str(self.request.user.agency_id) != str(user.agency_id):
                logger.warning(f"User {self.request.user.id} attempted to reactivate user {user.id} from different agency")
                raise PermissionDenied(detail="You don't have permission to reactivate this user")

            # Agency admins can only reactivate agents
            if self.request.user.role == 'Agency_Admin' and user.role != 'Agent':
                logger.warning(f"Agency admin {self.request.user.id} attempted to reactivate non-agent user {user.id}")
                raise PermissionDenied(detail="You can only reactivate agent accounts")

            return user

        except CustomUser.DoesNotExist:
            logger.error(f"User with ID {user_id} not found")
            raise NotFound(detail=f"User with ID {user_id} not found")

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        logger.info(f"Reactivating user: {user.email}")

        try:
            user.is_active = True
            user.save()
            logger.info(f"Successfully reactivated user {user.id}")

            return Response({
                'status': 'success',
                'message': 'User account reactivated successfully',
                'data': {
                    'id': user.id,
                    'email': user.email,
                    'name': f"{user.first_name} {user.last_name}",
                    'is_active': user.is_active
                }
            })

        except Exception as e:
            logger.error(f"Error reactivating user: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'An error occurred while reactivating the user account'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PasswordResetRequestView(generics.GenericAPIView):
    """
    View for requesting a password reset
    """
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = User.objects.get(email=serializer.validated_data['email'])
            # Create verification token
            token = VerificationToken.objects.create(user=user)
            
            # Send password reset email
            context = {
                'user': user,
                'reset_url': f"{settings.FRONTEND_URL}/reset-password/{token.token}"
            }
            html_message = render_to_string('users/email/password_reset_email.html', context)
            plain_message = strip_tags(html_message)
            
            send_mail(
                'Reset your password',
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html_message,
                fail_silently=False,
            )

            return Response({
                'status': 'success',
                'message': 'Password reset email has been sent.'
            }, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            # We don't want to reveal that the user doesn't exist
            return Response({
                'status': 'success',
                'message': 'If an account exists with this email, you will receive a password reset link.'
            }, status=status.HTTP_200_OK)

class PasswordResetConfirmView(generics.GenericAPIView):
    """
    View for confirming password reset
    """
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            token = VerificationToken.objects.get(
                token=serializer.validated_data['token'],
                used=False
            )

            if token.is_expired():
                return Response({
                    'status': 'error',
                    'message': 'Password reset link has expired'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Update user's password
            user = token.user
            user.set_password(serializer.validated_data['password'])
            user.save()

            # Mark token as used
            token.used = True
            token.save()

            return Response({
                'status': 'success',
                'message': 'Password has been reset successfully'
            }, status=status.HTTP_200_OK)

        except VerificationToken.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Invalid or expired password reset link'
            }, status=status.HTTP_400_BAD_REQUEST)
