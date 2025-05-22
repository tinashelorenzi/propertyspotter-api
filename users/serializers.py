from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Agency, CustomUser, VerificationToken
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from datetime import datetime, timedelta

User = get_user_model()

class UserDetailSerializer(serializers.ModelSerializer):
    agency_name = serializers.CharField(source='agency.name', read_only=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'phone', 'role', 'agency', 'agency_name', 'profile_image_url',
            'created_at', 'is_active', 'profile_complete'
        ]
        read_only_fields = fields  # All fields are read-only

class AgencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Agency
        fields = ['id', 'name', 'email', 'phone', 'address', 'license_valid_until']
        read_only_fields = ['id']

    def create(self, validated_data):
        agency = Agency.objects.create(**validated_data)
        return agency

class UserRegistrationSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)
    agency = serializers.PrimaryKeyRelatedField(
        queryset=Agency.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'username', 'password', 'confirm_password',
            'first_name', 'last_name', 'phone', 'role', 'agency',
            'bank_name', 'bank_branch_code', 'account_number',
            'account_name', 'account_type'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'bank_name': {'required': False},
            'bank_branch_code': {'required': False},
            'account_number': {'required': False},
            'account_name': {'required': False},
            'account_type': {'required': False}
        }

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def create(self, validated_data):
        confirm_password = validated_data.pop('confirm_password')
        # Set is_active to False by default
        validated_data['is_active'] = False
        user = CustomUser.objects.create_user(**validated_data)
        
        # Create verification token
        token = VerificationToken.objects.create(user=user)
        
        # Send verification email
        context = {
            'user': user,
            'verification_url': f"{settings.FRONTEND_URL}/verify-email/{token.token}"
        }
        html_message = render_to_string('users/email/verification_email.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            'Verify your email address',
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return user

class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.CharField()

    def validate_token(self, value):
        try:
            token = VerificationToken.objects.get(token=value, used=False)
            if token.is_expired():
                raise serializers.ValidationError("Token has expired")
            return value
        except VerificationToken.DoesNotExist:
            raise serializers.ValidationError("Invalid token")

class EmailAuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField(label="Email")
    password = serializers.CharField(label="Password", style={'input_type': 'password'}, trim_whitespace=False)

    def validate(self, attrs):
        from django.contrib.auth import authenticate
        email = attrs.get('email')
        password = attrs.get('password')
        if email and password:
            user = authenticate(request=self.context.get('request'), username=email, password=password)
            if not user:
                # Try authenticating by email field
                from django.contrib.auth import get_user_model
                UserModel = get_user_model()
                try:
                    user_obj = UserModel.objects.get(email=email)
                    user = authenticate(request=self.context.get('request'), username=user_obj.username, password=password)
                except UserModel.DoesNotExist:
                    user = None
            if not user:
                raise serializers.ValidationError('Unable to log in with provided credentials.', code='authorization')
        else:
            raise serializers.ValidationError('Must include "email" and "password".', code='authorization')
        attrs['user'] = user
        return attrs 