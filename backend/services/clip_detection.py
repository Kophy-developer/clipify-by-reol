"""Clip detection: find 45–60s high-value segments from transcript/srt."""
from __future__ import annotations
import re
from pathlib import Path

from utils.config import settings

MIN_DURATION = 45.0
MAX_DURATION = 60.0

# Simple emotional/attention keywords (can expand)
KEYWORDS = {
    "important", "key", "critical", "remember", "best", "worst",
    "always", "never", "must", "secret", "truth", "actually",
    "surprising", "amazing", "incredible", "finally", "exactly",
}


def parse_srt(srt_path: str) -> list[tuple[float, float, str]]:
    """Return list of (start, end, text)."""
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()
    blocks = re.split(r"\n\s*\n", content.strip())
    out = []
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue
        # Line 0: index, Line 1: time, Line 2+: text
        time_line = lines[1]
        m = re.match(r"(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})", time_line)
        if not m:
            continue
        start = _parse_ts(m.group(1))
        end = _parse_ts(m.group(2))
        text = " ".join(lines[2:]).strip()
        if text:
            out.append((start, end, text))
    return out


def _parse_ts(s: str) -> float:
    part = s.replace(",", ".")
    h, m, s = part.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def score_sentence(text: str) -> float:
    """Higher = more valuable."""
    t = text.lower()
    score = 0.0
    words = len(t.split())
    if words >= 5:
        score += 0.2
    for kw in KEYWORDS:
        if kw in t:
            score += 0.15
    return min(score, 1.0)


def select_clip_segment(segments: list[tuple[float, float, str]]) -> dict | None:
    """
    Pick one 45–60s clip: group segments until duration in range.
    Prefer continuous speech, sentence boundaries, and keyword density.
    """
    if not segments:
        return None
    best = None
    best_score = -1.0

    i = 0
    while i < len(segments):
        start = segments[i][0]
        end = segments[i][1]
        texts = [segments[i][2]]
        j = i + 1
        while j < len(segments) and (segments[j][1] - start) <= MAX_DURATION:
            end = segments[j][1]
            texts.append(segments[j][2])
            duration = end - start
            if MIN_DURATION <= duration <= MAX_DURATION:
                # Score: length in range + speech density + keywords
                score = 0.3 * (1.0 - abs(duration - 52.5) / 15)  # prefer ~52s
                score += 0.3 * min(1.0, (j - i + 1) / 20)
                for t in texts:
                    score += 0.1 * score_sentence(t)
                if score > best_score:
                    best_score = score
                    best = {
                        "start_time": round(start, 1),
                        "end_time": round(end, 1),
                        "duration": round(duration, 1),
                        "confidence": round(min(1.0, score), 2),
                    }
            j += 1
        i += 1

    return best


MAX_CANDIDATES = 3


def select_all_clip_candidates(segments: list[tuple[float, float, str]], max_n: int = MAX_CANDIDATES) -> list[dict]:
    """Return up to max_n clip candidates (best first), each with start_time, end_time, duration, confidence."""
    if not segments:
        return []
    candidates: list[dict] = []
    seen_ranges: set[tuple[float, float]] = set()
    i = 0
    while i < len(segments) and len(candidates) < max_n:
        start = segments[i][0]
        end = segments[i][1]
        texts = [segments[i][2]]
        j = i + 1
        while j < len(segments) and (segments[j][1] - start) <= MAX_DURATION:
            end = segments[j][1]
            texts.append(segments[j][2])
            duration = end - start
            if MIN_DURATION <= duration <= MAX_DURATION:
                key = (round(start, 1), round(end, 1))
                if key not in seen_ranges:
                    seen_ranges.add(key)
                    score = 0.3 * (1.0 - abs(duration - 52.5) / 15)
                    score += 0.3 * min(1.0, (j - i + 1) / 20)
                    for t in texts:
                        score += 0.1 * score_sentence(t)
                    candidates.append({
                        "start_time": round(start, 1),
                        "end_time": round(end, 1),
                        "duration": round(duration, 1),
                        "confidence": round(min(1.0, score), 2),
                    })
            j += 1
        i += 1
    candidates.sort(key=lambda c: c["confidence"], reverse=True)
    return candidates[:max_n]


def detect_clips(srt_path: str) -> list[dict]:
    """Return list of clip candidates (best first, up to MAX_CANDIDATES). At least one 45–60s clip."""
    segments = parse_srt(srt_path)
    candidates = select_all_clip_candidates(segments)
    for idx, c in enumerate(candidates):
        c["clip_id"] = f"candidate_{idx}"
    return candidates
