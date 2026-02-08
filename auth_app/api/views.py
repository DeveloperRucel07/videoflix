from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth import get_user_model
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from auth_app.api.authentication import CookieJWTAuthentication
from auth_app.utils.activate_email import send_activation_email
from auth_app.utils.password_reset_email import send_password_reset_email
from core import settings
from .serializers import CustomTokenObtainPairSerializer, RegistrationSerializer, ResetPasswordSerializer, ConfirmPasswordResetSerializer


User = get_user_model()
class RegistrationView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        """  Handle user registration by validating the input data, creating a new user, and returning an appropriate response.

        Args:
            request (): The HTTP request object containing user registration data.

        Returns:
            Response: A response object indicating success or failure of the registration process.
        """
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.create(serializer.validated_data)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            # activation_link = f"{settings.FRONTEND_URL}/activate/{uid}/{token}"
            send_activation_email(request, user, uid, token)
            
            return Response({
                "token": token,
                "user": {
                    "id": user.id,
                    "username": user.email,
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class ActivateAccountView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, uidb64, token):
        """ Handle account activation by validating the provided UID and token, activating the user account if valid, and returning an appropriate response. 

        Args:
            request (request): The HTTP request object containing activation data.
            uidb64 (UID): The base64-encoded UID of the user to be activated.
            token (string):  The token used to validate the activation request.

        Returns:
            object: A response indicating success or failure of the activation process.
        """
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
            if default_token_generator.check_token(user, token):
                user.is_active = True
                user.save()
                return Response({"message": "Account successfully activated."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "The activation link is invalid or has expired."}, status=status.HTTP_400_BAD_REQUEST)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"error": "Invalid activation data."}, status=status.HTTP_400_BAD_REQUEST)
        
        
class CookieTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    def post(self, request, *args, **kwargs):
        '''Override the post method to set the JWT token in an HttpOnly cookie.
        Args:
            request (request): user request
        Returns:
            response: response with the JWT token set in an HttpOnly cookie.
        '''
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh = serializer.validated_data['refresh']
        access = serializer.validated_data['access']
        
        response = Response({'message':'Login successfully'}, status=status.HTTP_200_OK)
        response.set_cookie(
            key='access_token',
            value=str(access),
            httponly=True,
            secure=True,
            samesite='None',
        )
        response.set_cookie(
            key='refresh_token',
            value=str(refresh),
            httponly=True,
            secure=True,
            samesite='None',
        )
        data = {
            'detail': 'Login successfully!',
            'user': {
                'id': serializer.user.id,
                'username': serializer.user.email,
            }
        }
        response.data = data
        return response
    

class CookieTokenRefreshView(TokenRefreshView):
    """
    View for refreshing the access token using a cookie-based refresh token.
    """

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests for refreshing the access token.
        """
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            return Response(
                {"error": "Refresh token not found in cookies."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        serializer = self.get_serializer(data={"refresh": refresh_token})

        try:
            serializer.is_valid(raise_exception=True)
        except:
            return Response(
                {"error": "Refresh token invalid!."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        access_token = serializer.validated_data.get("access")

        response = Response({
            "detail": "Token refreshed",
            "access": access_token
        }, status=status.HTTP_200_OK)

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="None"
        )

        return response
    
    
class LogoutView(APIView):
    """
    View for logging out a user by clearing authentication cookies.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def post(self, request):
        """
        Handle POST requests for logging out a user.
        """
        response = Response(
            {"detail": "Log-Out successfully! All Tokens will be deleted. Refresh token is now invalid."}, status=status.HTTP_200_OK)
        
        token = RefreshToken(request.COOKIES.get("refresh_token"))
        token.blacklist()
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")

        return response


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    serializer_class = ResetPasswordSerializer
    def post(self, request):
        """ Handle password reset requests by validating the provided email, generating a password reset link if the user exists, and returning an appropriate response.

        Args:
            request (request): The HTTP request object containing the email for password reset.
        Returns:
            object: A response indicating success or failure of the password reset request process.
        """
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            send_password_reset_email(user, uid, token)
            return Response({
                "detail": "An email has been sent to reset your password.",
            }, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        

class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    serializer_class = ConfirmPasswordResetSerializer
    def post(self, request, uidb64, token):
        """ Handle password reset confirmation by validating the provided UID and token, allowing the user to set a new password if valid, and returning an appropriate response.

        Args:
            request (request): The HTTP request object containing the new password.
            uidb64 (UID): The base64-encoded UID of the user resetting their password.
            token (string): The token used to validate the password reset request.
        Returns:
            object: A response indicating success or failure of the password reset confirmation process.
        """
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
            if default_token_generator.check_token(user, token):
                serializer = self.serializer_class(data=request.data)
                if serializer.is_valid(raise_exception=True):
                    new_password = serializer.validated_data['new_password']
                    user.set_password(new_password)
                    user.save()
                    return Response({"detail": "Your Password has been successfully reset."}, status=status.HTTP_200_OK)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"error": "The password reset link is invalid or has expired."}, status=status.HTTP_400_BAD_REQUEST)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"error": "Invalid password reset data."}, status=status.HTTP_400_BAD_REQUEST)
        
        
        
        
        