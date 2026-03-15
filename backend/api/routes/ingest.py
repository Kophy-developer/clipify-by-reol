"""POST /ingest: accept URL or file upload, return job_id."""
import os
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from utils.job_store import create_job, update_job
from utils.job_store import JobStage
from utils.config import settings
from tasks.pipeline import run_pipeline

router = APIRouter()


class IngestURLResponse(BaseModel):
    job_id: str


@router.post("", response_model=IngestURLResponse)
async def ingest_video(
    url: str | None = Form(None),
    file: UploadFile | None = File(None),
    scheduled_at: str | None = Form(None),
):
    """Accept video URL or file upload. Optional scheduled_at (ISO) to publish at a later time."""
    if not url and not file:
        raise HTTPException(400, "Provide either 'url' or 'file'.")
    if url and file:
        raise HTTPException(400, "Provide only one of 'url' or 'file'.")

    job_id = create_job()

    if url:
        update_job(job_id, stage=JobStage.PENDING, message="URL submitted")
        run_pipeline.delay(job_id=job_id, source_url=url, scheduled_at=scheduled_at)
        return IngestURLResponse(job_id=job_id)

    # File upload
    ext = os.path.splitext(file.filename or "video.mp4")[1] or ".mp4"
    safe_name = f"{job_id}{ext}"
    path = settings.upload_dir / safe_name
    try:
        contents = await file.read()
        with open(path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(500, f"Save upload failed: {e}")

    update_job(job_id, stage=JobStage.PENDING, message="File uploaded")
    run_pipeline.delay(job_id=job_id, source_path=str(path), scheduled_at=scheduled_at)
    return IngestURLResponse(job_id=job_id)
