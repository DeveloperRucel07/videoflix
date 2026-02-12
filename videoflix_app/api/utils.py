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



def convert_video_to_hls(video_id):
    try:
        video = Video.objects.get(pk=video_id)
        source_path = video.video_file.path
    except Video.DoesNotExist:
        print(f"Video {video_id} not found.")
        return

    base_output_dir = Path(settings.MEDIA_ROOT) / "hls" / str(video_id)
    base_output_dir.mkdir(parents=True, exist_ok=True)

    # name, width, bitrate, maxrate, bufsize
    renditions = [
        ("480p", 854, "1400k", "1500k", "2100k"),
        ("720p", 1280, "2800k", "3000k", "4200k"),
        ("1080p", 1920, "5000k", "5500k", "7500k"),
    ]

    filter_parts = []
    var_stream_map = []

    cmd = [
        "ffmpeg",
        "-y",
        "-i", source_path,
        "-filter_complex"
    ]

    # Build scaling filters
    for idx, (name, width, *_ ) in enumerate(renditions):
        filter_parts.append(
            f"[0:v]scale=w={width}:h=-2[v{idx}]"
        )

    cmd.append("; ".join(filter_parts))

    # Map each resolution
    for idx, (name, _, bitrate, maxrate, bufsize) in enumerate(renditions):
        (base_output_dir / name).mkdir(exist_ok=True)

        cmd.extend([
            "-map", f"[v{idx}]",
            "-map", "0:a",
            f"-b:v:{idx}", bitrate,
            f"-maxrate:v:{idx}", maxrate,
            f"-bufsize:v:{idx}", bufsize,
        ])

        var_stream_map.append(f"v:{idx},a:{idx},name:{name}")

    cmd.extend([
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-g", "48",
        "-keyint_min", "48",
        "-sc_threshold", "0",
        "-f", "hls",
        "-hls_time", "6",
        "-hls_playlist_type", "vod",
        "-hls_segment_filename",
        str(base_output_dir / "%v" / "%03d.ts"),
        "-master_pl_name", "index.m3u8",
        "-var_stream_map", " ".join(var_stream_map),
        str(base_output_dir / "%v" / "index.m3u8"),
    ])

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f" HLS conversion finished for video {video_id}")
    except subprocess.CalledProcessError as e:
        print("HLS conversion failed:")
        print(e.stderr)



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
        convert_video_to_hls(video_id)
        source_path = video.video_file.path
        resolutions = [480, 720, 1080]
        # for resolution in resolutions:
        #     convert_to_hls(video_id, source_path, resolution)
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
    

