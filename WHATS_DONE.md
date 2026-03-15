# What’s Done (one‑liners)

- **Ingest:** Accept video URL or file upload; validate; download with yt-dlp or save file.
- **Transcribe:** Extract audio, run faster-whisper, output SRT with timestamps.
- **Clip detection:** Pick 45–60s segment from transcript (speech density, keywords); up to 3 candidates.
- **Render:** Cut segment, 9:16 1080×1920, H.264/AAC; try loudnorm, fallback simple; face-aware crop when a face is detected.
- **Subtitles:** Wrap to 42 chars/line, max 2 lines; shift to clip start; burn in with FFmpeg.
- **Validation:** Check duration 45–60s and resolution 1080×1920; fail job if invalid.
- **Publish:** Stub TikTok / Instagram / YouTube; 3 retries per platform; optional platforms filter via env.
- **API:** POST /ingest (URL or file, optional scheduled_at), GET /status/{id}, GET /results/{id}, GET /results/{id}/clip (download), POST /retry/{clip_id}.
- **Job store:** Redis (or in-memory); clip_id → job_id for retry.
- **Scheduling:** Optional scheduled_at on ingest; Celery Beat runs scheduled publishes every minute and cleanup daily.
- **Raw cleanup:** Delete source video after successful pipeline; retention task deletes old files after N days.
- **Frontend:** URL or file input, optional “publish later” time, status polling, results with preview + download link, retry failed uploads.
- **No auth** by default; API keys doc for when you add real social posting.
- **Docs:** README, LOCALHOST.md, API_KEYS_AND_INTEGRATIONS.md, scripts/start-local.sh.
