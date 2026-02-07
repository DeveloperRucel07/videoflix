
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from auth_app.api.authentication import CookieJWTAuthentication

from videoflix_app.models import Video
from .serializers import VideoSerializer

class VideoListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    queryset = Video.objects.all().order_by('-created_at')
    serializer_class = VideoSerializer