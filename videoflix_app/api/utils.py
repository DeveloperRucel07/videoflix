import subprocess, json
import os
from django.conf import settings
from pathlib import Path
from videoflix_app.models import Video 
import logging

logger = logging.getLogger(__name__)


def _get_resolution(path):
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "json", path
    ]
    data = json.loads(subprocess.run(cmd, capture_output=True, text=True).stdout)
    if not data.get("streams"):
        raise ValueError("No video stream found")
    w, h = data["streams"][0]["width"], data["streams"][0]["height"]
    if not w or not h:
        raise ValueError("Invalid video resolution")
    return w, h


def create_video_thumbnail(video_id):
    """
        Generates a visually representative thumbnail using ffmpeg's thumbnail filter.
        Avoids black frames automatically.
    """
    try:
        video = Video.objects.get(pk=video_id)
    except Video.DoesNotExist:
        logger.warning("Video %s not found while creating thumbnail.", video_id)
        return

    thumb_dir = Path(settings.MEDIA_ROOT) / "thumbnail"
    thumb_dir.mkdir(parents=True, exist_ok=True)
    thumb_path = thumb_dir / f"{video_id}.jpg"

    cmd = [
        "ffmpeg", "-y", "-i", video.video_file.path,
        "-vf", "thumbnail,scale=1280:-1",
        "-frames:v", "1", "-q:v", "2",
        str(thumb_path)
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        video.thumbnail_url = f"thumbnail/{video_id}.jpg"
        video.save(update_fields=["thumbnail_url"])
        logger.info("Thumbnail created for video %s at %s", video_id, thumb_path)

    except subprocess.CalledProcessError as e:
        logger.error("Thumbnail creation failed for video %s: %s", video_id, e.stderr)


# def convert_video_to_hls(video_id):
#     try:
#         video = Video.objects.get(pk=video_id)
#     except Video.DoesNotExist:
#         logger.warning("Video %s not found for HLS conversion.", video_id)
#         return

#     out_dir = Path(settings.VIDEO_ROOT) / str(video_id)
#     out_dir.mkdir(parents=True, exist_ok=True)

#     renditions = [
#         ("480p", 854, "1400k", "1500k", "2100k"),
#         ("720p", 1280, "2800k", "3000k", "4200k"),
#         ("1080p", 1920, "5000k", "5500k", "7500k"),
#     ]

#     filters, stream_map = [], []
#     cmd = ["ffmpeg", "-y", "-i", video.video_file.path, "-filter_complex"]

#     for i, (name, w, *_ ) in enumerate(renditions):
#         filters.append(f"[0:v]scale=w='min({w},iw)':h=-2[v{i}]")

#     cmd.append(";".join(filters))

#     for i, (name, _, br, mr, buf) in enumerate(renditions):
#         (out_dir / name).mkdir(exist_ok=True)
#         cmd += [
#             "-map", f"[v{i}]", "-map", "0:a",
#             f"-b:v:{i}", br, f"-maxrate:v:{i}", mr, f"-bufsize:v:{i}", buf
#         ]
#         stream_map.append(f"v:{i},a:{i},name:{name}")

#     cmd += [
#         "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
#         "-c:a", "aac", "-b:a", "128k",
#         "-g", "48", "-keyint_min", "48", "-sc_threshold", "0",
#         "-f", "hls", "-hls_time", "6", "-hls_playlist_type", "vod",
#         "-hls_segment_filename", str(out_dir / "%v/%03d.ts"),
#         "-master_pl_name", "index.m3u8",
#         "-var_stream_map", " ".join(stream_map),
#         str(out_dir / "%v/index.m3u8"),
#     ]

#     try:
#         subprocess.run(cmd, check=True, capture_output=True, text=True)
#         logger.info("HLS conversion finished for video %s", video_id)

#     except subprocess.CalledProcessError as e:
#         logger.error("HLS conversion failed for video %s: %s", video_id, e.stderr)

#     try:
#         video = Video.objects.get(pk=video_id)
#     except Video.DoesNotExist:
#         logger.warning("Video %s not found for HLS conversion.", video_id)
#         return

#     out_dir = Path(settings.VIDEO_ROOT) / str(video_id)
#     out_dir.mkdir(parents=True, exist_ok=True)

#     manifest_path = out_dir / "index.m3u8"
#     segment_pattern = out_dir / "%03d.ts"

#     cmd = [
#         "ffmpeg",
#         "-y",
#         "-i", video.video_file.path,

#         # Video encoding
#         "-c:v", "libx264",
#         "-preset", "veryfast",
#         "-crf", "23",

#         # Audio encoding
#         "-c:a", "aac",
#         "-b:a", "128k",

#         # HLS settings
#         "-f", "hls",
#         "-hls_time", "6",
#         "-hls_playlist_type", "vod",
#         "-hls_segment_filename", str(segment_pattern),

#         str(manifest_path),
#     ]

#     try:
#         subprocess.run(cmd, check=True, capture_output=True, text=True)
#         logger.info("HLS (single bitrate) conversion finished for video %s", video_id)

#     except subprocess.CalledProcessError as e:
#         logger.error("HLS conversion failed for video %s: %s", video_id, e.stderr)

def convert_video_to_hls(video_id):
    video = Video.objects.filter(pk=video_id).first()
    if not video:
        logger.warning("Video %s not found.", video_id)
        return
    width, _ = _get_resolution(video.video_file.path)
    if width < 240:
        raise ValueError(f"Video too small for HLS ({width}px width)")

    out_dir = Path(settings.VIDEO_ROOT) / str(video_id)
    out_dir.mkdir(parents=True, exist_ok=True)

    renditions = [
        ("480p", 854, "1400k", "1500k", "2100k"),
        ("720p", 1280, "2800k", "3000k", "4200k"),
        ("1080p", 1920, "5000k", "5500k", "7500k"),
    ]

    renditions = [r for r in renditions if r[1] <= width]
    if not renditions:
        raise ValueError("No valid renditions for this video")

    filters = ";".join(
        f"[0:v]scale=w='min({w},iw)':h=-2[v{i}]"
        for i, (_, w, *_ ) in enumerate(renditions)
    )

    stream_map = " ".join(f"v:{i},a:{i},name:{name}" for i, (name, *_ ) in enumerate(renditions))

    cmd = [
        "ffmpeg", "-y", "-i", video.video_file.path,
        "-filter_complex", filters,
        *sum([
            [
                "-map", f"[v{i}]", "-map", "0:a",
                f"-b:v:{i}", br, f"-maxrate:v:{i}", mr, f"-bufsize:v:{i}", buf
            ]
            for i, (_, _, br, mr, buf) in enumerate(renditions)
        ], []),

        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-g", "48", "-keyint_min", "48", "-sc_threshold", "0",
        "-f", "hls", "-hls_time", "6", "-hls_playlist_type", "vod",
        "-hls_segment_filename", str(out_dir / "%v/%03d.ts"),
        "-master_pl_name", "index.m3u8",
        "-var_stream_map", stream_map,
        str(out_dir / "%v/index.m3u8"),
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info("HLS conversion finished for video %s", video_id)
    except subprocess.CalledProcessError as e:
        logger.error("HLS conversion failed for video %s: %s", video_id, e.stderr)


def convert_and_save(video_id):

    """ 
        convert_and_save is a helper function that retrieves the video by its ID, 
        converts it to HLS format using the convert_to_hls function, and updates the conversion status in the database. 
        If any error occurs during the conversion process, it updates the conversion status to 'failed' and saves the error message.
        Args:
            video_id (int): The ID of the video to be converted and saved.
    """
    video = Video.objects.filter(id=video_id).first()

    if not video:
        logger.warning("convert_and_save called with non-existent video %s", video_id)
        return

    try:
        logger.info("Starting processing pipeline for video %s", video_id)

        create_video_thumbnail(video_id)
        convert_video_to_hls(video_id)
        video.conversion_status = "completed"
        video.error_message = ""

        logger.info("Processing completed for video %s", video_id)

    except Exception as e:
        video.conversion_status = "failed"
        video.error_message = str(e)

        logger.exception("Processing failed for video %s", video_id)

    finally:
        video.save()

