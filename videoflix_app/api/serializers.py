from rest_framework import serializers
from videoflix_app.models import Video


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = [
            'id',
            'created_at',
            'title',
            'description',
            'thumbnail_url',
            'category',
        ]

    def get_thumbnail_as_img(self, obj):
        if obj.thumbnail_url:
            return obj.thumbnail_url.url.replace('.png', '.jpg')
        return None