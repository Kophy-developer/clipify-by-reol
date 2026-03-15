"""Face detection for biasing crop toward speaker. Returns (center_x_ratio, center_y_ratio) or None."""
from __future__ import annotations
import subprocess
import tempfile
from pathlib import Path


def get_face_center_ratio(video_path: str, at_time: float = 0.0) -> tuple[float, float] | None:
    """
    Extract one frame at at_time, detect face, return (x_ratio, y_ratio) in 0–1.
    If no face found, return None (caller uses center crop).
    """
    try:
        import cv2
    except ImportError:
        return None
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        frame_path = f.name
    try:
        cmd = [
            "ffmpeg", "-y", "-ss", str(at_time), "-i", video_path,
            "-vframes", "1", "-q:v", "2", frame_path,
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if r.returncode != 0:
            return None
        img = cv2.imread(frame_path)
        if img is None:
            return None
        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        if len(faces) == 0:
            return None
        # Use largest face
        x, y, fw, fh = max(faces, key=lambda r: r[2] * r[3])
        cx = x + fw / 2
        cy = y + fh / 2
        return (cx / w, cy / h)
    except Exception:
        return None
    finally:
        try:
            Path(frame_path).unlink(missing_ok=True)
        except OSError:
            pass
