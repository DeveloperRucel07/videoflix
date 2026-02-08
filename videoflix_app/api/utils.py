import subprocess
import os
from django.conf import settings
from pathlib import Path
from videoflix_app.models import Video 


def convert_to_hls(video_id, video_path, resolution):
    output_dir = os.path.join(settings.MEDIA_ROOT, 'hls', str(video_id), f"{resolution}p")
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, "index.m3u8")
    
    cmd = (
        f"ffmpeg -i {video_path} -vf scale=-2:{resolution} "
        f"-start_number 0 -hls_time 10 -hls_list_size 0 -f hls {output_path}"
    )
    subprocess.run(cmd, shell=True, check=True)



def convert_and_save(video_id):
    """ 
        convert_and_save is a helper function that retrieves the video by its ID, 
        converts it to HLS format using the convert_to_hls function, and updates the conversion status in the database. 
        If any error occurs during the conversion process, it updates the conversion status to 'failed' and saves the error message.
        Args:
            video_id (int): The ID of the video to be converted and saved.
    """
    try:
        video = Video.objects.get(id=video_id)
        source_path = video.video_file.path
        resolutions = [480, 720, 1080]
        for resolution in resolutions:
            convert_to_hls(video_id, source_path, resolution)
        video.conversion_status = 'completed'
        video.error_message = ''
    except Exception as e:
        video = Video.objects.filter(id=video_id).first()
        if video:
            video.conversion_status = 'failed'
            video.error_message = str(e)
    finally:
        if video:
            video.save()
    
    

