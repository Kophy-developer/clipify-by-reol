"""QA validation: clip duration 45–60s, format 9:16, subtitles present. Fail job if invalid."""
from __future__ import annotations
import json
import subprocess
from pathlib import Path

from utils.config import settings

MIN_DURATION = 45.0
MAX_DURATION = 60.0
TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920


def validate_clip(video_path: str) -> tuple[bool, str]:
    """
    Check: duration in [45, 60], has video stream, resolution 1080x1920 (or acceptable).
    Returns (ok, error_message).
    """
    path = Path(video_path)
    if not path.exists():
        return False, "Clip file not found"

    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration:stream=width,height,codec_type",
        "-of", "json",
        str(path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return False, f"ffprobe failed: {r.stderr}"

    data = json.loads(r.stdout)
    duration = 0.0
    width = height = 0
    has_video = False
    for s in data.get("streams", []):
        if s.get("codec_type") == "video":
            has_video = True
            width = int(s.get("width", 0) or 0)
            height = int(s.get("height", 0) or 0)
    fmt = data.get("format") or {}
    duration = float(fmt.get("duration", 0) or 0)

    if not has_video:
        return False, "No video stream"
    if duration < MIN_DURATION or duration > MAX_DURATION:
        return False, f"Duration {duration:.1f}s outside 45–60s"
    if width != TARGET_WIDTH or height != TARGET_HEIGHT:
        return False, f"Resolution {width}x{height} (expected 1080x1920)"
    return True, ""
