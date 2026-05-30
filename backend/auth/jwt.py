"""
JWT Token Management
---------------------
Creates and validates JWT access tokens.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict

from jose import JWTError, jwt
from core.config import settings

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"


def create_access_token(
    data: Dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        data:          Payload to encode (usually {"sub": user_id})
        expires_delta: Token lifetime (defaults to 24 hours)

    Returns:
        Signed JWT token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=24))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[Dict]:
    """
    Decode and validate a JWT token.

    Returns:
        Decoded payload dict, or None if invalid/expired
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode failed: {e}")
        return None


def get_user_id_from_token(token: str) -> Optional[str]:
    """Extract user_id from a valid token."""
    payload = decode_token(token)
    if payload:
        return payload.get("sub")
    return None