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
        """
            Dynamically build thumbnail URL based on video ID
        """
        request = self.context.get('request')
        path = f"/media/thumbnail/{obj.id}.jpg"
        if request:
            return request.build_absolute_uri(path)
        return path