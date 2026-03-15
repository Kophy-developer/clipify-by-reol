"""Application configuration."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """App settings from env."""

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_key: str = ""  # If set, require X-API-Key header (internal access)

    # Paths
    base_dir: Path = Path(__file__).resolve().parent.parent
    upload_dir: Path = Path("/tmp/clipify_uploads")
    output_dir: Path = Path("/tmp/clipify_output")
    clip_retention_days: int = 7

    # Celery / Redis
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # Clip rules (seconds)
    clip_min_seconds: float = 45.0
    clip_max_seconds: float = 60.0

    # Social (optional; for real posting)
    tiktok_access_token: str = ""
    instagram_access_token: str = ""
    youtube_client_secrets_path: str = ""
    # Platforms to publish to (subset of tiktok, instagram, youtube); empty = all
    publish_platforms: str = ""  # e.g. "tiktok,instagram,youtube" or "tiktok"

    # Job store: use Redis when set; else in-memory (single-worker only)
    use_redis_job_store: bool = True

    # yt-dlp: optional path to cookies file for YouTube (avoids "Sign in to confirm you're not a bot")
    yt_dlp_cookies_path: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


def ensure_dirs(settings: Settings) -> None:
    """Create upload and output directories."""
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.output_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
ensure_dirs(settings)
