"""Video ingestion: URL download (yt-dlp) or use uploaded file. Validate format and length."""
from __future__ import annotations
import subprocess
from pathlib import Path
from typing import Any

from utils.config import settings


def get_video_duration_seconds(path: str) -> float:
    """Get duration in seconds via ffprobe."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        path,
    ]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if out.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {out.stderr}")
    return float(out.stdout.strip())


def get_video_metadata(path: str) -> dict[str, Any]:
    """Get duration, resolution, and audio presence."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration:stream=width,height,codec_type",
        "-of", "json",
        path,
    ]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if out.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {out.stderr}")

    import json
    data = json.loads(out.stdout)
    duration = 0.0
    width = height = 0
    has_audio = False
    for s in data.get("streams", []):
        if s.get("codec_type") == "video":
            width = int(s.get("width", 0) or 0)
            height = int(s.get("height", 0) or 0)
        if s.get("codec_type") == "audio":
            has_audio = True
    fmt = data.get("format")
    if isinstance(fmt, dict) and "duration" in fmt:
        duration = float(fmt.get("duration", 0) or 0)
    return {
        "duration_seconds": duration or get_video_duration_seconds(path),
        "width": width,
        "height": height,
        "has_audio": has_audio,
    }


def download_from_url(url: str, job_id: str) -> str:
    """Download video from URL with yt-dlp. Returns path to local file."""
    out_path = settings.upload_dir / f"{job_id}.%(ext)s"
    cmd = [
        "yt-dlp",
        "--no-playlist",
        "-f", "best[ext=mp4]/best",
        "-o", str(out_path),
        url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp failed: {result.stderr}")

    # yt-dlp replaces %(ext)s; find the file
    base = settings.upload_dir / job_id
    for p in settings.upload_dir.glob(f"{job_id}.*"):
        if p.suffix in (".mp4", ".mkv", ".webm", ".mov"):
            return str(p)
    raise FileNotFoundError(f"Downloaded file not found under {base}")


def ensure_video_file(source_path: str | None, source_url: str | None, job_id: str) -> tuple[str, dict]:
    """Return (local_video_path, metadata). Download if URL, else validate upload. Fails if duration < clip_min."""
    if source_url:
        path = download_from_url(source_url, job_id)
    elif source_path and Path(source_path).exists():
        path = source_path
    else:
        raise ValueError("Need source_path or source_url")
    meta = get_video_metadata(path)
    duration = meta.get("duration_seconds") or 0
    if duration < settings.clip_min_seconds:
        raise ValueError(
            f"Video too short: {duration:.1f}s. Need at least {settings.clip_min_seconds}s to create a 45–60s clip."
        )
    return path, meta
