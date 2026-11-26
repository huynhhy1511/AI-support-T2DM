from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
import jwt

from app.core.config import settings

ALGORITHM = "HS256"


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a stored bcrypt hash."""
    if not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except ValueError:
        return False


def create_access_token(
    subject: str, expires_delta: Optional[timedelta] = None
) -> str:
    """Create a signed JWT access token."""
    now = datetime.now(timezone.utc)
    if expires_delta is not None:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode: Dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT access token."""
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
