from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model, authenticate
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings

User = get_user_model()

class RegistrationSerializer(serializers.ModelSerializer):
    confirmed_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [ 'email', 'password', 'confirmed_password']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
        }
        
    def validate_confirmed_password(self, value):
        """ Validate that the confirmed password matches the original password.
            Args:
                value (str): The confirmed password to validate.
            Raises:
                serializers.ValidationError: If the confirmed password does not match the original password.
            Returns:
                str: The validated confirmed password.
        """
        if 'password' in self.initial_data and value != self.initial_data['password']:
            raise serializers.ValidationError("The confirmed password does not match the original password.")
        return value
    
    def validate_email(self, value):
        """ Validate that the email is unique in the system.
            Args:
                value (str): The email address to validate.
            Raises:
                serializers.ValidationError: If a user with the provided email already exists.
            Returns:
                str: The validated email address.
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def create(self, validated_data):
        """ Create and save a new user instance with the validated data.
            Returns:
                User: The newly created user instance.
        """
        validated_data.pop('confirmed_password')
        user = User(
            username=validated_data['email'].partition("@")[0],
            email=validated_data['email'],
            password=validated_data['password'],
            is_active=False,
        )
        user.set_password(validated_data['password'])
        user.is_active= False
        user.save()
        return user   
    
    
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom Token Obtain Pair Serializer.
    Used to customize the token claims if needed.
    Currently, it does not add any additional claims.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)  
    
    def __init__(self, *args, **kwargs):
        """
        Initializes the serializer and removes the 'username' field.
        """
        super().__init__(*args, **kwargs)

        if "username" in self.fields:
            self.fields.pop("username")
    
    
    def validate(self, attrs):
        """
        Validates the user's credentials.
        Checks the email and password, ensures the user exists and is active.
        If the credentials are valid, the username is added for token generation.
        """
        email = attrs.get('email')
        password = attrs.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"detail": "email or password does not exist."})

        if not user.check_password(password):
            raise serializers.ValidationError({"detail": "invalid credentials."})

        if not user.is_active:
            raise serializers.ValidationError(
                {"detail": "Account is not active. Please check your email for the activation link."}
            )

        attrs['username'] = user.username
        data = super().validate(attrs)
        return data
    
class ResetPasswordSerializer(serializers.Serializer):
    """
    Serializer for handling password reset requests.
    Validates the email and generates a password reset link if the user exists.
    """
    email = serializers.EmailField()
    
    def validate_email(self, value):
        """ Validate that the email exists in the system.
            Args:
                value (str): The email address to validate.
            Raises:
                serializers.ValidationError: If a user with the provided email does not exist.
            Returns:
                str: The validated email address.
        """
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value
    
    
class ConfirmPasswordResetSerializer(serializers.Serializer):
    """
    Serializer for confirming password reset.
    Validates the new password and its confirmation.
    """
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        """ Validate that the new password and confirm password match.
            Args:
                attrs (dict): The data containing new_password and confirm_password.
            Raises:
                serializers.ValidationError: If the new password and confirm password do not match.
            Returns:
                dict: The validated data if the passwords match.
        """
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')

        if new_password != confirm_password:
            raise serializers.ValidationError("The new password and confirm password do not match.")
        
        return attrs
    
        
        
    
    
        
  
    