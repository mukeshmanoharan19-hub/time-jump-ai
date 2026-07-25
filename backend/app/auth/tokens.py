import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from app.config import settings


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def session_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=settings.session_ttl_hours)
