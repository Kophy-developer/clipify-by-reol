# Clipify by Reol

AI-powered pipeline: accept a video URL or upload → generate 45–60s vertical clips with burned-in subtitles → auto-publish to TikTok, Instagram Reels, and YouTube Shorts.

## Stack

- **Backend:** Python, FastAPI, Celery, Redis, FFmpeg, yt-dlp, faster-whisper
- **Frontend:** React (Vite), TailwindCSS
- **APIs:** Internal REST; no authentication by default. Social posting uses stubs until you add API keys – see **API_KEYS_AND_INTEGRATIONS.md** for which keys are needed (TikTok, Instagram, YouTube).

## Prerequisites

- Python 3.10+
- Node 18+
- FFmpeg (with libx264, aac)
- Redis (for Celery)
- (Optional) GPU for faster Whisper

## Quick start

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp ../.env.example .env     # edit if needed
```

Ensure Redis is running, then from the **backend** directory:

```bash
cd backend
# Terminal 1: API
uvicorn main:app --reload --host 0.0.0.0

# Terminal 2: Worker
celery -A celery_app worker -l info -c 1
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Use “Video URL” or “Upload file”, then “Generate clip”. The app polls status and shows results when done.

Frontend `vite.config.js` proxies `/ingest`, `/status`, `/results`, `/retry` to `http://localhost:8000`.

## API

When `API_KEY` is set in `.env`, all requests must include header `X-API-Key: <API_KEY>`. Frontend: set `VITE_API_KEY` to the same value so the app sends it.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ingest` | Body: `url=...` or `file=...` (multipart); optional `scheduled_at=...` (ISO). Returns `{ "job_id": "uuid" }`. |
| GET | `/status/{job_id}` | Processing state and message. |
| GET | `/results/{job_id}` | Published links and clip metadata (includes `clip_id` for retry). |
| POST | `/retry/{clip_id}` | Re-run publish for that clip; poll `/status/{job_id}` for result. |

## Pipeline

1. **Ingest** — Download from URL (yt-dlp) or use uploaded file; validate with ffprobe.
2. **Transcribe** — Extract audio, faster-whisper, full SRT (millisecond precision).
3. **Clip detection** — 45–60s segment (speech density, sentence boundaries, scoring).
4. **Render** — FFmpeg: cut, 9:16 (1080×1920), H.264/AAC; face-aware crop when a face is detected.
5. **Subtitles** — SRT wrapped to 42 chars/line, max 2 lines; shifted to clip start; burned in (centered).
6. **Validation** — QA: duration 45–60s, resolution 1080×1920; job fails if invalid.
7. **Publish** — Up to 3 retries per platform; optional `scheduled_at` to publish later. Raw video is deleted after success.

Job state is stored in **Redis** (or in-memory if Redis is off). Clip retention: files in upload/output dirs older than `CLIP_RETENTION_DAYS` are deleted by a daily Beat task.

## Scheduling

- **Immediate:** Omit `scheduled_at`; publish runs right after render.
- **Later:** Send `scheduled_at` (e.g. `2025-02-12T09:00:00`) with `/ingest`. Pipeline runs up to render, then job stays in `scheduled` until the time; **Celery Beat** runs `run_scheduled_publishes` every minute and publishes when due.

Run Beat so scheduled posts and retention run:

```bash
celery -A celery_app beat -l info
```

## Hosting

- **Backend:** e.g. Google Cloud Run, DigitalOcean App Platform ($5–10/mo).
- **Frontend:** Netlify or Vercel (static build).
- **Worker:** Same app platform or a separate worker process; ensure Redis is available.

## License

Internal use only.
