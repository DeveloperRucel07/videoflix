from django.conf import settings
from django.dispatch import receiver
from django.db import transaction
from django.db.models.signals import post_save, post_delete
import django_rq

from videoflix_app.models import Video
from .utils import  convert_and_save


@receiver(post_save, sender=Video)
def video_post_save(sender, instance, created, **kwargs):
    if created:
        Video.objects.filter(pk=instance.pk).update(conversion_status='processing')
        transaction.on_commit(lambda: django_rq.enqueue(convert_and_save, instance.id))
          
            
@receiver(post_delete, sender=Video)
def auto_delete_video_on_delete(sender, instance, **kwargs):
    """
    Deletes original video and HLS segments when a Video object is deleted.
    """
    from pathlib import Path
    import shutil
    
    if instance.video_file:
        file_path = Path(instance.video_file.path)
        if file_path.is_file():
            try:
                file_path.unlink()
            except Exception as e:
                print(f"Error deleting file {file_path}: {e}")

    hls_dir = Path(settings.MEDIA_ROOT) / "hls" / str(instance.id)
    if hls_dir.exists() and hls_dir.is_dir():
        try:
            shutil.rmtree(hls_dir)
        except Exception as e:
            print(f"Error deleting HLS folder {hls_dir}: {e}")
