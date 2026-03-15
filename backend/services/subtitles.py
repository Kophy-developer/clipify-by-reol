"""Subtitle burn-in: align SRT to clip timestamps, burn into video. FFmpeg."""
from __future__ import annotations
import re
from pathlib import Path

MAX_CHARS_PER_LINE = 42
MAX_LINES = 2


def wrap_subtitle_text(text: str, max_chars: int = MAX_CHARS_PER_LINE, max_lines: int = MAX_LINES) -> str:
    """Format text: max 42 chars per line, max 2 lines. Word-boundary only (no mid-word break)."""
    text = (text or "").strip()
    if not text:
        return ""
    words = text.split()
    lines: list[str] = []
    current = ""
    for w in words:
        candidate = f"{current} {w}".strip() if current else w
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                lines.append(current)
            if len(lines) >= max_lines:
                break
            current = w if len(w) <= max_chars else w[: max_chars - 1] + "…"
    if current and len(lines) < max_lines:
        lines.append(current)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
    if lines and len(lines[-1]) > max_chars:
        lines[-1] = lines[-1][: max_chars - 1] + "…"
    return "\n".join(lines)


def shift_srt(srt_path: str, offset_seconds: float, output_path: str) -> None:
    """Write new SRT with timestamps shifted and text wrapped (42 chars/line, max 2 lines)."""
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()
    blocks = re.split(r"\n\s*\n", content.strip())
    out_lines = []
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue
        out_lines.append(lines[0])
        start_s = _parse_ts_srt(lines[1].split("-->")[0].strip())
        end_s = _parse_ts_srt(lines[1].split("-->")[1].strip())
        start_s = max(0, start_s - offset_seconds)
        end_s = max(0, end_s - offset_seconds)
        out_lines.append(f"{_to_srt_ts(start_s)} --> {_to_srt_ts(end_s)}")
        raw_text = " ".join(lines[2:]).strip()
        wrapped = wrap_subtitle_text(raw_text)
        if wrapped:
            out_lines.append(wrapped)
        out_lines.append("")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines))


def _parse_ts_srt(s: str) -> float:
    s = s.replace(",", ".")
    h, m, rest = s.split(":")
    sec, ms = rest.split(".")
    return int(h) * 3600 + int(m) * 60 + int(sec) + int(ms[:3]) / 1000.0


def _to_srt_ts(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def burn_subtitles(video_path: str, srt_path: str, output_path: str) -> None:
    """
    Burn SRT into video. Centered, sans-serif, readable on mobile.
    Escape path for ffmpeg filter.
    """
    # Escape single quotes in path for filter_complex
    srt_esc = srt_path.replace("\\", "\\\\").replace("'", "'\\\\''")
    # Subtitles filter: force_style for font, size, position
    filter_str = (
        f"subtitles='{srt_esc}'"
        ":force_style='FontName=Sans,FontSize=24,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,Outline=2,Alignment=2,MarginV=80'"
    )
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", filter_str,
        "-c:a", "copy",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-movflags", "+faststart",
        output_path,
    ]
    import subprocess
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg burn subtitles failed: {r.stderr}")
