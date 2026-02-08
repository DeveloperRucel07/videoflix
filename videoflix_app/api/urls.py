from django.urls import path
from videoflix_app.api.views import VideoHlsSegmentView, VideoHlsStreamManifestView, VideoListView

urlpatterns = [
    path("video/", VideoListView.as_view(), name="video-list"),
    path("video/<int:video_id>/<str:resolution>/index.m3u8", VideoHlsStreamManifestView.as_view(), name="video-hls-manifest"),
    path("video/<int:video_id>/<str:resolution>/<str:segment>", VideoHlsSegmentView.as_view(), name="video-hls-segment"),
    
]