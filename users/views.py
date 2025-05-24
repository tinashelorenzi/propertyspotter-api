from django.shortcuts import render
from rest_framework import generics, status
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
    UserProfileUpdateSerializer
)
from .models import VerificationToken, Agency, CustomUser
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from django.shortcuts import get_object_or_404

User = get_user_model()

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
