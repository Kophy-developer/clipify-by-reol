"""POST /retry/{clip_id}: retry failed upload for a clip."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from utils.job_store import get_job_id_by_clip_id, get_job
from tasks.pipeline import retry_publish_clip

router = APIRouter()


class RetryResponse(BaseModel):
    clip_id: str
    message: str
    job_id: str | None = None


@router.post("/{clip_id}", response_model=RetryResponse)
async def retry_upload(clip_id: str):
    """Find job for clip_id, re-run publish to all platforms, update job results."""
    job_id = get_job_id_by_clip_id(clip_id)
    if not job_id:
        raise HTTPException(404, "Clip or job not found")
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    # Enqueue so we don't block; client can poll GET /status/{job_id}
    retry_publish_clip.delay(clip_id)
    return RetryResponse(
        clip_id=clip_id,
        message="Retry enqueued; poll GET /status/{job_id} for result",
        job_id=job_id,
    )