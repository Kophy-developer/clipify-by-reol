#!/usr/bin/env bash
# Start Clipify locally. Run each block in a SEPARATE terminal (or use the one-liners below).
#
# Terminal 1 – Redis (if you have it):
#   redis-server
#
# Terminal 2 – Backend API:
#   cd backend && . .venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000
#
# Terminal 3 – Celery worker:
#   cd backend && . .venv/bin/activate && celery -A celery_app worker -l info -c 1
#
# Terminal 4 – Frontend:
#   cd frontend && npm run dev
#
# Then open http://localhost:5173

set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"

echo "Clipify by Reol – local start"
echo "=============================="
echo ""
echo "First-time setup:"
echo "  1. Backend:  cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt"
echo "  2. Frontend: cd frontend && npm install"
echo "  3. Have Redis running (brew install redis && redis-server) and FFmpeg (brew install ffmpeg)"
echo ""
echo "Then run in 4 separate terminals:"
echo "  Terminal 1: redis-server"
echo "  Terminal 2: cd $BACKEND && . .venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000"
echo "  Terminal 3: cd $BACKEND && . .venv/bin/activate && celery -A celery_app worker -l info -c 1"
echo "  Terminal 4: cd $FRONTEND && npm run dev"
echo ""
echo "Open http://localhost:5173"
echo ""

# If run with --api, start only the API (for single-terminal quick test)
if [ "$1" = "--api" ]; then
  cd "$BACKEND"
  . .venv/bin/activate
  uvicorn main:app --host 0.0.0.0 --port 8000
  exit 0
fi

# If run with --frontend, start only the frontend
if [ "$1" = "--frontend" ]; then
  cd "$FRONTEND"
  npm run dev
  exit 0
fi
