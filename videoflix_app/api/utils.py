import subprocess, json
import os
from django.conf import settings
from pathlib import Path
from videoflix_app.models import Video 
import logging

logger = logging.getLogger(__name__)


def _get_resolution(path):
    """
        Extract the resolution (width and height) of a video file using ffprobe.

        This function executes an FFmpeg probe command to inspect the first video
        stream (`v:0`) of the given file and returns its width and height. The
        output is parsed from JSON into Python data.

        Args:
            path (str or Path): Filesystem path to the video file.

        Returns:
            tuple[int, int]: A tuple containing (width, height) of the video.

        Raises:
            ValueError:
                - If no video stream is found in the file
                - If the extracted width or height is missing or invalid
    """


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


def convert_video_to_hls(video_id):

    """
    Convert a video file into HLS (HTTP Live Streaming) format.

    This function retrieves a video from the database, validates its resolution,
    and uses FFmpeg to generate a single-bitrate HLS stream. The output consists
    of an `.m3u8` playlist file and multiple `.ts` segment files, which can be
    served for streaming.

    The conversion uses CRF-based encoding for adaptive quality and does not
    perform scaling or multiple renditions, ensuring compatibility with all
    video sizes.

    Args:
        video_id (int): The primary key of the Video instance to convert.

    Raises:
        ValueError: If the video has an invalid or too small resolution.
        subprocess.CalledProcessError: If the FFmpeg process fails.
    """
    video = Video.objects.filter(pk=video_id).first()
    if not video:
        logger.warning("Video %s not found.", video_id)
        return

    width, height = _get_resolution(video.video_file.path)
    if not width or not height or width < 240:
        raise ValueError(f"Invalid video resolution: {width}x{height}")

    out_dir = Path(settings.VIDEO_ROOT) / str(video_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = out_dir / "index.m3u8"
    segments = out_dir / "%03d.ts"

    cmd = [
        "ffmpeg",
        "-y",
        "-i", video.video_file.path,
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
        "-hls_segment_filename", str(segments),
        str(manifest),
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info("HLS conversion (single bitrate) finished for video %s", video_id)

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

