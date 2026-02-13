from rest_framework import serializers
from videoflix_app.models import Video


class VideoSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()
    class Meta:
        model = Video
        fields = [
            'id',
            'title',
            'description',
            'category',
            'thumbnail_url',
            'created_at',
        ]

    def get_thumbnail_url(self, obj):
        if obj.thumbnail_url:
            return obj.thumbnail_url.url
        return None