from rest_framework_simplejwt.authentication import JWTAuthentication

class CookieJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication class that retrieves the token from cookies.
    """
    def authenticate(self, request):

        access_token = request.COOKIES.get("access_token")

        if access_token:
            validated_token = self.get_validated_token(access_token)
            user = self.get_user(validated_token)
            return (user, validated_token)

        return super().authenticate(request)