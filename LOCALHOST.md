# Run Clipify on localhost

## One-time setup

1. **Backend (from project root)**  
   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
   First run can take several minutes (e.g. OpenCV, faster-whisper).

2. **Frontend**  
   ```bash
   cd frontend
   npm install
   ```

3. **Redis** (required for the worker)  
   - macOS: `brew install redis && redis-server`  
   - Or run Redis in Docker.

4. **FFmpeg** (required for video processing)  
   - macOS: `brew install ffmpeg`

---

## Start the app (4 terminals)

**Terminal 1 – Redis**
```bash
redis-server
```

**Terminal 2 – Backend API**
```bash
cd backend
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Terminal 3 – Celery worker**
```bash
cd backend
source .venv/bin/activate
celery -A celery_app worker -l info -c 1
```

**Terminal 4 – Frontend**
```bash
cd frontend
npm run dev
```

Then open **http://localhost:5173** in your browser.

---

## Troubleshooting

**`pip install` fails with SSL / certificate errors (macOS)**  
- Upgrade pip: `python3 -m pip install --upgrade pip`  
- Or use trusted host: `pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org`

**OpenCV builds from source and fails (e.g. cmake)**  
- We pin `opencv-python-headless==4.9.0.80` so pip uses a prebuilt wheel where possible. If your platform has no wheel, install CMake and build tools, or try: `pip install opencv-python-headless --only-binary :all:` (may install a different version).

---

## Optional: Celery Beat (scheduled posts + retention)

To run scheduled publishes and daily clip cleanup:

```bash
cd backend && source .venv/bin/activate && celery -A celery_app beat -l info
```

Run this in addition to the worker.
