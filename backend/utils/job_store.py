"""Job state store: Redis (production, multi-worker) or in-memory fallback."""
from __future__ import annotations
import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from utils.config import settings

# In-memory fallback when Redis disabled or unavailable
_memory_jobs: dict[str, dict[str, Any]] = {}
_memory_clip_to_job: dict[str, str] = {}

_redis_client: Any = None


def _get_redis():
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    if not getattr(settings, "use_redis_job_store", True):
        return None
    try:
        import redis
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        _redis_client.ping()
        return _redis_client
    except Exception:
        return None


class JobStage(str, Enum):
    PENDING = "pending"
    INGESTING = "ingesting"
    TRANSCRIBING = "transcribing"
    DETECTING_CLIPS = "detecting_clips"
    RENDERING = "rendering"
    BURNING_SUBTITLES = "burning_subtitles"
    PUBLISHING = "publishing"
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    FAILED = "failed"


def create_job() -> str:
    job_id = str(uuid.uuid4())
    rec = {
        "job_id": job_id,
        "stage": JobStage.PENDING.value,
        "message": "",
        "video_path": None,
        "metadata": {},
        "transcript": None,
        "srt_path": None,
        "clips": [],
        "results": [],
        "published_clips": [],
        "error": None,
        "scheduled_at": None,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    r = _get_redis()
    if r:
        r.set(f"job:{job_id}", json.dumps(rec), ex=86400 * 30)
    else:
        _memory_jobs[job_id] = rec
    return job_id


def get_job(job_id: str) -> dict | None:
    r = _get_redis()
    if r:
        raw = r.get(f"job:{job_id}")
        if not raw:
            return None
        return json.loads(raw)
    return _memory_jobs.get(job_id)


def update_job(
    job_id: str,
    *,
    stage: JobStage | None = None,
    message: str | None = None,
    video_path: str | None = None,
    metadata: dict | None = None,
    transcript: str | None = None,
    srt_path: str | None = None,
    clips: list | None = None,
    results: list | None = None,
    published_clips: list | None = None,
    error: str | None = None,
    scheduled_at: str | None = None,
) -> None:
    rec = get_job(job_id)
    if not rec:
        return
    if stage is not None:
        rec["stage"] = stage.value
    if message is not None:
        rec["message"] = message
    if video_path is not None:
        rec["video_path"] = video_path
    if metadata is not None:
        rec["metadata"] = metadata
    if transcript is not None:
        rec["transcript"] = transcript
    if srt_path is not None:
        rec["srt_path"] = srt_path
    if clips is not None:
        rec["clips"] = clips
    if results is not None:
        rec["results"] = results
    if published_clips is not None:
        rec["published_clips"] = published_clips
    if error is not None:
        rec["error"] = error
    if scheduled_at is not None:
        rec["scheduled_at"] = scheduled_at
    rec["updated_at"] = datetime.utcnow().isoformat()

    r = _get_redis()
    if r:
        r.set(f"job:{job_id}", json.dumps(rec), ex=86400 * 30)
    else:
        _memory_jobs[job_id] = rec


def set_job_stage(job_id: str, stage: JobStage, message: str = "") -> None:
    update_job(job_id, stage=stage, message=message)


def register_clip_job(clip_id: str, job_id: str) -> None:
    """Map clip_id -> job_id for POST /retry/{clip_id}."""
    r = _get_redis()
    if r:
        r.set(f"clip:{clip_id}", job_id, ex=86400 * 30)
    else:
        _memory_clip_to_job[clip_id] = job_id


def get_job_id_by_clip_id(clip_id: str) -> str | None:
    r = _get_redis()
    if r:
        return r.get(f"clip:{clip_id}")
    return _memory_clip_to_job.get(clip_id)


_scheduled_jobs: set[str] = set()


def add_scheduled_job(job_id: str) -> None:
    r = _get_redis()
    if r:
        r.sadd("scheduled_jobs", job_id)
    else:
        _scheduled_jobs.add(job_id)


def remove_scheduled_job(job_id: str) -> None:
    r = _get_redis()
    if r:
        r.srem("scheduled_jobs", job_id)
    else:
        _scheduled_jobs.discard(job_id)


def get_scheduled_job_ids() -> list[str]:
    r = _get_redis()
    if r:
        return list(r.smembers("scheduled_jobs") or [])
    return [jid for jid, rec in _memory_jobs.items() if rec.get("stage") == JobStage.SCHEDULED.value]
