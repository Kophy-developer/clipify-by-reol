"""Internal API auth: require X-API-Key when API_KEY is set."""
from fastapi import Header, HTTPException

from utils.config import settings


async def require_api_key(x_api_key: str | None = Header(None, alias="X-API-Key")) -> None:
    """If settings.api_key is set, require X-API-Key header to match. Otherwise no check."""
    if not settings.api_key:
        return
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(401, "Invalid or missing API key")
