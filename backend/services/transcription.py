"""Transcription and SRT generation using faster-whisper (free, local)."""
from __future__ import annotations
from pathlib import Path

from utils.config import settings


def extract_audio(video_path: str, output_path: str) -> None:
    """Extract audio to WAV for Whisper."""
    import subprocess
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        output_path,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg extract audio failed: {r.stderr}")


def transcribe_and_srt(audio_path: str, job_id: str) -> tuple[str, str]:
    """Transcribe audio with faster-whisper; return (transcript_text, srt_path)."""
    from faster_whisper import Whisper
    model = Whisper("base", device="cpu", compute_type="int8")
    segments, info = model.transcribe(audio_path, word_timestamps=True)

    lines: list[str] = []
    full_text_parts: list[str] = []
    idx = 1
    for s in segments:
        start = s.start
        end = s.end
        text = (s.text or "").strip()
        if not text:
            continue
        full_text_parts.append(text)
        # SRT: millisecond precision
        lines.append(str(idx))
        lines.append(
            f"{_ts(s.start)} --> {_ts(s.end)}"
        )
        lines.append(text)
        lines.append("")
        idx += 1

    transcript = " ".join(full_text_parts)
    srt_path = str(Path(settings.output_dir) / f"{job_id}_full.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return transcript, srt_path


def _ts(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
