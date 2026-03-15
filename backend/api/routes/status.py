"""GET /status/{job_id}: return processing state."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from utils.job_store import get_job, JobStage

router = APIRouter()


class StatusResponse(BaseModel):
    job_id: str
    stage: str
    message: str
    error: str | None
    created_at: str
    updated_at: str


@router.get("/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str):
    """Return current processing state for the job."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return StatusResponse(
        job_id=job["job_id"],
        stage=job["stage"],
        message=job.get("message", ""),
        error=job.get("error"),
        created_at=job["created_at"],
        updated_at=job["updated_at"],
    )
