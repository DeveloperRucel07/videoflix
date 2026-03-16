from django.db import models

class Video(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    video_file = models.FileField(upload_to='video/')
    thumbnail_url = models.ImageField(upload_to="thumbnail/", blank=True, null=True)
    category = models.CharField(max_length=100, null=False, blank=False, default="Learning")
    conversion_status = models.CharField(
        max_length=20, 
        default='pending', 
        blank=True, 
        null=True 
    )

    def __str__(self):
        return self.title