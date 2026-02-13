import subprocess
import os
from django.conf import settings
from pathlib import Path
from videoflix_app.models import Video 


def create_video_thumbnail(video_id):
    """
    Generates a visually representative thumbnail using ffmpeg's thumbnail filter.
    Avoids black frames automatically.
    """
    try:
        video = Video.objects.get(pk=video_id)
        source_path = video.video_file.path
    except Video.DoesNotExist:
        print(f"❌ Video {video_id} not found.")
        return

    thumbnail_dir = Path(settings.MEDIA_ROOT) / "thumbnail"
    thumbnail_dir.mkdir(parents=True, exist_ok=True)

    thumbnail_path = thumbnail_dir / f"{video_id}.jpg"

    cmd = [
        "ffmpeg",
        "-y",
        "-i", source_path,
        "-vf", "thumbnail,scale=1280:-1",  # auto-select good frame + resize
        "-frames:v", "1",
        "-q:v", "2",
        str(thumbnail_path),
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        relative_path = f"thumbnail/{video_id}.jpg"
        Video.objects.filter(pk=video_id).update(
            thumbnail_url=relative_path
        )
        print(f"✅ Smart thumbnail created for video {video_id} at {thumbnail_path}")
        print(f"Thumbnail URL: {relative_path}")

    except subprocess.CalledProcessError as e:
        print("❌ Thumbnail creation failed:")
        print(e.stderr)


def convert_video_to_hls(video_id):
    try:
        video = Video.objects.get(pk=video_id)
        source_path = video.video_file.path
    except Video.DoesNotExist:
        print(f"Video {video_id} not found.")
        return

    base_output_dir = Path(settings.MEDIA_ROOT) / "hls" / str(video_id)
    base_output_dir.mkdir(parents=True, exist_ok=True)

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

    for idx, (name, width, *_ ) in enumerate(renditions):
        filter_parts.append(
            f"[0:v]scale=w={width}:h=-2[v{idx}]"
        )

    cmd.append("; ".join(filter_parts))
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
        create_video_thumbnail(video_id)
        convert_video_to_hls(video_id)
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
    

