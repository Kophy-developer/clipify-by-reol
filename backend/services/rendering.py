"""Clip rendering: cut segment, convert to 9:16, center or face-biased crop. FFmpeg."""
from __future__ import annotations
import subprocess
from pathlib import Path

from utils.config import settings

OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920


def _crop_filter(face_center_ratio: tuple[float, float] | None) -> str:
    """Scale to cover 1080x1920, then crop. If face_center_ratio, bias crop toward face."""
    scale = "scale=iw*max(1080/iw\\,1920/ih):ih*max(1080/iw\\,1920/ih)"
    if face_center_ratio is None:
        return f"{scale},crop=1080:1920:(iw-1080)/2:(ih-1920)/2"
    fx, fy = face_center_ratio
    # Crop so face center (fx*iw, fy*ih) ends up at (540, 960)
    crop_x = f"max(0\\,min(floor(iw*{fx:.4f})-540\\,iw-1080))"
    crop_y = f"max(0\\,min(floor(ih*{fy:.4f})-960\\,ih-1920))"
    return f"{scale},crop=1080:1920:{crop_x}:{crop_y}"


def render_clip(
    video_path: str,
    start_time: float,
    end_time: float,
    output_path: str,
    face_center_ratio: tuple[float, float] | None = None,
) -> None:
    """
    Cut segment and convert to 9:16 (1080x1920). Optional face-aware crop. H.264, AAC, loudnorm.
    """
    filter_complex = _crop_filter(face_center_ratio)
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_time),
        "-to", str(end_time),
        "-i", video_path,
        "-vf", filter_complex,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-af", "loudnorm",
        "-movflags", "+faststart",
        output_path,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg render failed: {r.stderr}")


def render_clip_simple(
    video_path: str,
    start_time: float,
    end_time: float,
    output_path: str,
    face_center_ratio: tuple[float, float] | None = None,
) -> None:
    """Render to 9:16. Optionally bias crop toward face (from face_detect.get_face_center_ratio)."""
    filter_complex = _crop_filter(face_center_ratio)
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_time),
        "-to", str(end_time),
        "-i", video_path,
        "-vf", filter_complex,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        output_path,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg render failed: {r.stderr}")
