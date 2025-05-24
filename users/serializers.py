from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Agency, CustomUser, VerificationToken, InvitationToken
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from datetime import datetime, timedelta
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()

class AgencyAgentsSerializer(serializers.ModelSerializer):
    """
    Serializer for listing agents within an agency
    """
    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'phone', 'role', 'profile_image_url', 'created_at',
            'is_active', 'profile_complete', 'last_login'
        ]
        read_only_fields = fields

class UserDetailSerializer(serializers.ModelSerializer):
    agency_name = serializers.CharField(source='agency.name', read_only=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'phone', 'role', 'agency', 'agency_name', 'profile_image_url',
            'created_at', 'is_active', 'profile_complete',
            'bank_name', 'bank_branch_code', 'account_number',
            'account_name', 'account_type'
        ]
        read_only_fields = fields  # All fields are read-only

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'phone', 'password',
            'bank_name', 'bank_branch_code', 'account_number',
            'account_name', 'account_type'
        ]
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
            'phone': {'required': False},
            'password': {'required': False},
            'bank_name': {'required': False},
            'bank_branch_code': {'required': False},
            'account_number': {'required': False},
            'account_name': {'required': False},
            'account_type': {'required': False}
        }
    
    def update(self, instance, validated_data):
        # Only update fields that are provided
        if 'first_name' in validated_data:
            instance.first_name = validated_data['first_name']
        if 'last_name' in validated_data:
            instance.last_name = validated_data['last_name']
        if 'phone' in validated_data:
            instance.phone = validated_data['phone']
        if 'password' in validated_data:
            instance.set_password(validated_data['password'])
        if 'bank_name' in validated_data:
            instance.bank_name = validated_data['bank_name']
        if 'bank_branch_code' in validated_data:
            instance.bank_branch_code = validated_data['bank_branch_code']
        if 'account_number' in validated_data:
            instance.account_number = validated_data['account_number']
        if 'account_name' in validated_data:
            instance.account_name = validated_data['account_name']
        if 'account_type' in validated_data:
            instance.account_type = validated_data['account_type']
        instance.save()
        return instance

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

class AgentInvitationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    phone = serializers.CharField(max_length=20)

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

class PasswordSetSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords do not match.")
        
        try:
            validate_password(data['password'])
        except ValidationError as e:
            raise serializers.ValidationError({'password': list(e.messages)})
        
        return data 