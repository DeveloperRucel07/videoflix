from django.contrib import admin

from .models import Video

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('id','title', 'description', 'created_at', 'category', 'thumbnail_url', 'video_file', 'conversion_status')
    search_fields = ('title', 'description')
    list_filter = ('created_at', 'category')
