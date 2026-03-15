"""Pipeline: ingest -> transcribe -> detect -> render -> burn -> validate -> publish (or schedule)."""
from __future__ import annotations
import os
import uuid
from datetime import datetime

from celery_app import app
from utils.config import settings
from utils.job_store import (
    update_job,
    set_job_stage,
    get_job,
    register_clip_job,
    add_scheduled_job,
    remove_scheduled_job,
    get_scheduled_job_ids,
    JobStage,
)
from services.ingestion import ensure_video_file, get_video_metadata
from services.transcription import extract_audio, transcribe_and_srt
from services.clip_detection import detect_clips
from services.face_detect import get_face_center_ratio
from services.rendering import render_clip, render_clip_simple
from services.subtitles import shift_srt, burn_subtitles
from services.validation import validate_clip
from services.publishing import publish_all


@app.task(bind=True, name="tasks.pipeline.run_pipeline")
def run_pipeline(
    self,
    job_id: str,
    source_url: str | None = None,
    source_path: str | None = None,
    scheduled_at: str | None = None,
):
    video_path: str | None = None
    try:
        # 1. Ingest
        set_job_stage(job_id, JobStage.INGESTING, "Downloading or validating video")
        video_path, metadata = ensure_video_file(source_path, source_url, job_id)
        update_job(job_id, video_path=video_path, metadata=metadata)

        # 2. Transcribe
        set_job_stage(job_id, JobStage.TRANSCRIBING, "Transcribing audio")
        audio_path = str(settings.output_dir / f"{job_id}_audio.wav")
        extract_audio(video_path, audio_path)
        transcript, srt_path = transcribe_and_srt(audio_path, job_id)
        update_job(job_id, transcript=transcript, srt_path=srt_path)
        try:
            os.remove(audio_path)
        except OSError:
            pass

        # 3. Detect clips (45–60s)
        set_job_stage(job_id, JobStage.DETECTING_CLIPS, "Detecting clip segments")
        clips = detect_clips(srt_path)
        if not clips:
            update_job(
                job_id,
                stage=JobStage.FAILED,
                error="No 45–60s segment found",
            )
            return
        clip = clips[0]
        clip["clip_id"] = str(uuid.uuid4())
        update_job(job_id, clips=clips)

        start = clip["start_time"]
        end = clip["end_time"]

        # 4. Render (face-aware crop when possible; try loudnorm, fallback to simple)
        set_job_stage(job_id, JobStage.RENDERING, "Rendering clip")
        face_ratio = get_face_center_ratio(video_path, at_time=start)
        raw_clip_path = str(settings.output_dir / f"{job_id}_clip_raw.mp4")
        try:
            render_clip(video_path, start, end, raw_clip_path, face_center_ratio=face_ratio)
        except Exception:
            render_clip_simple(video_path, start, end, raw_clip_path, face_center_ratio=face_ratio)

        set_job_stage(job_id, JobStage.BURNING_SUBTITLES, "Burning subtitles")
        clip_srt = str(settings.output_dir / f"{job_id}_clip.srt")
        shift_srt(srt_path, start, clip_srt)
        final_clip_path = str(settings.output_dir / f"{job_id}_final.mp4")
        burn_subtitles(raw_clip_path, clip_srt, final_clip_path)
        try:
            os.remove(raw_clip_path)
        except OSError:
            pass

        # 5. QA validation
        ok, err = validate_clip(final_clip_path)
        if not ok:
            update_job(job_id, stage=JobStage.FAILED, error=f"Validation failed: {err}")
            return

        caption = (transcript[:200] + "…") if len(transcript) > 200 else transcript
        title = caption[:100]

        # 6. Schedule or publish
        if scheduled_at:
            try:
                at = datetime.fromisoformat(scheduled_at.replace("Z", "+00:00"))
                if at.tzinfo is None:
                    at = at.replace(tzinfo=datetime.utcnow().astimezone().tzinfo)
                if at > datetime.now().astimezone(at.tzinfo):
                    published_clips = [{"clip_id": clip["clip_id"], "path": final_clip_path}]
                    update_job(
                        job_id,
                        stage=JobStage.SCHEDULED,
                        message="Waiting for scheduled time",
                        scheduled_at=scheduled_at,
                        published_clips=published_clips,
                    )
                    register_clip_job(clip["clip_id"], job_id)
                    add_scheduled_job(job_id)
                    # Raw video cleanup still below for immediate path; for scheduled we keep it until publish
                    return
            except Exception:
                pass

        set_job_stage(job_id, JobStage.PUBLISHING, "Publishing to social")
        results = publish_all(final_clip_path, caption=caption, title=title)
        published_clips = [{"clip_id": clip["clip_id"], "path": final_clip_path}]
        update_job(
            job_id,
            results=results,
            published_clips=published_clips,
            stage=JobStage.COMPLETED,
            message="Done",
        )
        register_clip_job(clip["clip_id"], job_id)

        # 7. Raw video cleanup after successful processing
        if video_path and os.path.isfile(video_path):
            try:
                os.remove(video_path)
            except OSError:
                pass

    except Exception as e:
        update_job(job_id, stage=JobStage.FAILED, error=str(e))
        raise


@app.task(name="tasks.pipeline.retry_publish_clip")
def retry_publish_clip(clip_id: str) -> dict:
    """Re-run publish for one clip. Used by POST /retry/{clip_id}."""
    from utils.job_store import get_job_id_by_clip_id, get_job, update_job, JobStage

    job_id = get_job_id_by_clip_id(clip_id)
    if not job_id:
        return {"ok": False, "error": "Clip or job not found"}
    job = get_job(job_id)
    if not job:
        return {"ok": False, "error": "Job not found"}
    published = job.get("published_clips") or []
    path = None
    for pc in published:
        if pc.get("clip_id") == clip_id:
            path = pc.get("path")
            break
    if not path or not os.path.isfile(path):
        return {"ok": False, "error": "Clip file not found or expired"}
    transcript = (job.get("transcript") or "")[:200]
    caption = transcript + ("…" if len(transcript) >= 200 else "")
    title = caption[:100]
    update_job(job_id, stage=JobStage.PUBLISHING, message="Retrying publish")
    results = publish_all(path, caption=caption, title=title)
    # Merge into job results (replace by platform)
    existing = {r["platform"]: r for r in job.get("results") or []}
    for r in results:
        existing[r["platform"]] = r
    update_job(job_id, results=list(existing.values()), stage=JobStage.COMPLETED, message="Done")
    return {"ok": True, "results": results}


@app.task(name="tasks.pipeline.cleanup_old_clips")
def cleanup_old_clips() -> dict:
    """Delete files in upload_dir and output_dir older than clip_retention_days."""
    import time
    from pathlib import Path

    now = time.time()
    max_age_sec = settings.clip_retention_days * 86400
    deleted_upload = 0
    deleted_output = 0
    for d in [settings.upload_dir, settings.output_dir]:
        if not d.exists():
            continue
        for p in Path(d).iterdir():
            if not p.is_file():
                continue
            try:
                if now - p.stat().st_mtime > max_age_sec:
                    p.unlink()
                    if d == settings.upload_dir:
                        deleted_upload += 1
                    else:
                        deleted_output += 1
            except OSError:
                pass
    return {"deleted_upload": deleted_upload, "deleted_output": deleted_output}


@app.task(name="tasks.pipeline.run_scheduled_publishes")
def run_scheduled_publishes() -> dict:
    """Run publish for jobs in stage=scheduled whose scheduled_at <= now."""
    from utils.job_store import get_job, update_job, remove_scheduled_job, get_scheduled_job_ids, JobStage

    job_ids = get_scheduled_job_ids()
    done = 0
    for job_id in job_ids:
        job = get_job(job_id)
        if not job or job.get("stage") != JobStage.SCHEDULED.value:
            remove_scheduled_job(job_id)
            continue
        scheduled_at = job.get("scheduled_at")
        if not scheduled_at:
            continue
        try:
            at = datetime.fromisoformat(scheduled_at.replace("Z", "+00:00"))
            if at.tzinfo is None:
                at = at.replace(tzinfo=datetime.utcnow().astimezone().tzinfo)
            if at > datetime.now().astimezone(at.tzinfo):
                continue
        except Exception:
            continue
        published = job.get("published_clips") or []
        if not published:
            continue
        path = published[0].get("path")
        if not path or not os.path.isfile(path):
            update_job(job_id, stage=JobStage.FAILED, error="Scheduled clip file missing")
            remove_scheduled_job(job_id)
            continue
        caption = (job.get("transcript") or "")[:200] + "…"
        title = caption[:100]
        update_job(job_id, stage=JobStage.PUBLISHING, message="Scheduled publish")
        results = publish_all(path, caption=caption, title=title)
        update_job(job_id, results=results, stage=JobStage.COMPLETED, message="Done")
        remove_scheduled_job(job_id)
        done += 1
    return {"published": done}
