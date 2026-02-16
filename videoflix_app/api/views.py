
from click import Path
from django.http import FileResponse, Http404
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from auth_app.api.authentication import CookieJWTAuthentication

from core import settings
from videoflix_app.models import Video
from .serializers import VideoSerializer

HLS_CONTENT_TYPE = 'application/vnd.apple.mpegurl'
TS_CONTENT_TYPE = "video/MP2T"  
class VideoListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    queryset = Video.objects.all().order_by('-created_at')
    serializer_class = VideoSerializer
    

class VideoHlsStreamManifestView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]
    BASE_DIR = settings.VIDEO_ROOT
    
    def get(self, request, *args, **kwargs):
        movie_id = kwargs.get('video_id')
        resolution = kwargs.get('resolution')
        if not (movie_id and resolution):
            raise Http404("Video or resolution not specified")
        
        candidate = (self.BASE_DIR / str(movie_id) / resolution / 'index.m3u8').resolve()
        print("HLS manifest path:", candidate)
        if not str(candidate).startswith(str(self.BASE_DIR.resolve())):
            raise Http404('Invalid HLS manifest path')

        if not candidate.is_file():
            raise Http404('HLS manifest not found')
        
        response = FileResponse(open(candidate, 'rb'), content_type=HLS_CONTENT_TYPE.lower())
        return response


class VideoHlsSegmentView(APIView):
    """
    Serve HLS video segments from MEDIA_ROOT/video/<movie_id>/<resolution>/<segment>.ts
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    BASE_DIR = settings.VIDEO_ROOT

    def get(self, request, movie_id=None, resolution=None, segment=None, *args, **kwargs):

        if not (movie_id and resolution and segment):
            raise Http404("Segment not specified")
        candidate = (self.BASE_DIR / str(movie_id) / resolution / segment).resolve()
        print("HLS segment path:", candidate)
        if not str(candidate).startswith(str(self.BASE_DIR.resolve())):
            raise Http404("Invalid segment path")
        if not candidate.is_file():
            raise Http404("Segment not found")
        response = FileResponse(open(candidate, "rb"), content_type=TS_CONTENT_TYPE.lower())
        return response


    
        