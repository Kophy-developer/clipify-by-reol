"""GET /results/{job_id}: return published clip links and artifacts. GET /results/{job_id}/clip: download final video."""
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from utils.job_store import get_job

router = APIRouter()


class PublishResult(BaseModel):
    platform: str
    status: str
    url: str | None = None
    error: str | None = None


class ResultsResponse(BaseModel):
    job_id: str
    stage: str
    results: list[PublishResult]
    clips: list[dict]
    error: str | None
    clip_url: str | None = None


def _get_final_clip_path(job_id: str) -> Path | None:
    job = get_job(job_id)
    if not job:
        return None
    published = job.get("published_clips") or []
    if not published:
        return None
    path = published[0].get("path")
    if not path:
        return None
    p = Path(path)
    return p if p.exists() else None


@router.get("/{job_id}", response_model=ResultsResponse)
async def get_results(job_id: str):
    """Return published clip links and clip metadata. clip_url is set when a final clip exists (for preview/download)."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    results = [PublishResult(**r) for r in job.get("results", [])]
    clip_url = None
    if _get_final_clip_path(job_id):
        clip_url = f"/results/{job_id}/clip"
    return ResultsResponse(
        job_id=job["job_id"],
        stage=job["stage"],
        results=results,
        clips=job.get("clips", []),
        error=job.get("error"),
        clip_url=clip_url,
    )


@router.get("/{job_id}/clip")
async def get_result_clip(job_id: str):
    """Stream the final rendered clip for preview or download. 404 if job missing or file expired."""
    path = _get_final_clip_path(job_id)
    if not path:
        raise HTTPException(404, "Clip not found or expired")
    return FileResponse(
        path,
        media_type="video/mp4",
        filename=f"clipify-{job_id[:8]}.mp4",
    )
