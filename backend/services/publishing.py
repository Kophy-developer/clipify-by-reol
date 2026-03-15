"""Social publishing: TikTok, Instagram Reels, YouTube Shorts. 3x retry per platform."""
from __future__ import annotations
import time
import uuid
from typing import Any, Callable

from utils.config import settings

# Real implementations: TikTok Content Posting API, Instagram Graph API, YouTube Data API v3.
# See API_KEYS_AND_INTEGRATIONS.md. Set tokens in settings and replace stub bodies below.


MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = [2, 5, 10]


def _publish_with_retry(
    fn: Callable[..., dict],
    *args: Any,
    **kwargs: Any,
) -> dict:
    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BACKOFF_SECONDS[min(attempt, len(RETRY_BACKOFF_SECONDS) - 1)])
    platform = getattr(fn, "__name__", "publish").replace("publish_to_", "")
    return {
        "platform": platform,
        "status": "failed",
        "url": None,
        "error": str(last_error) if last_error else "Unknown",
    }


def publish_to_tiktok(video_path: str, caption: str, **kwargs: Any) -> dict:
    """Upload to TikTok. Stub; replace with real API when token set."""
    return {
        "platform": "tiktok",
        "status": "published",
        "url": f"https://www.tiktok.com/@clipify/video/{uuid.uuid4().hex[:12]}",
    }


def publish_to_instagram(video_path: str, caption: str, **kwargs: Any) -> dict:
    """Upload to Instagram Reels. Stub."""
    return {
        "platform": "instagram",
        "status": "published",
        "url": f"https://www.instagram.com/reel/{uuid.uuid4().hex[:12]}/",
    }


def publish_to_youtube(video_path: str, caption: str, title: str, **kwargs: Any) -> dict:
    """Upload to YouTube Shorts. Stub."""
    return {
        "platform": "youtube",
        "status": "published",
        "url": f"https://www.youtube.com/shorts/{uuid.uuid4().hex}",
    }


def _get_platforms_filter() -> list[str]:
    """If publish_platforms is set (e.g. 'tiktok,instagram'), return allowed list; else all."""
    raw = getattr(settings, "publish_platforms", "") or ""
    if not raw.strip():
        return ["tiktok", "instagram", "youtube"]
    return [p.strip().lower() for p in raw.split(",") if p.strip()]


def publish_all(video_path: str, caption: str, title: str | None = None) -> list[dict]:
    """Publish to selected platforms (or all) with up to 3 retries each."""
    title = title or caption[:100]
    allowed = _get_platforms_filter()
    platform_fns = [
        ("tiktok", lambda: _publish_with_retry(publish_to_tiktok, video_path, caption)),
        ("instagram", lambda: _publish_with_retry(publish_to_instagram, video_path, caption)),
        ("youtube", lambda: _publish_with_retry(publish_to_youtube, video_path, caption, title=title)),
    ]
    results = []
    for name, fn in platform_fns:
        if name not in allowed:
            continue
        results.append(fn())
    return results
