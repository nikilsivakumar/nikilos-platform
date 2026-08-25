"""
Password hashing and JWT creation/verification. Nothing in here talks to
the database or to FastAPI directly -- deps.py wires this to real requests,
the same separation-of-concerns pattern used for permissions.py.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings

# bcrypt via passlib -- pinned versions (passlib==1.7.4, bcrypt==4.0.1) are
# required together; newer bcrypt breaks passlib's version probing.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: int) -> str:
    """
    Issues a JWT whose only real payload is the user's id (as 'sub', the
    standard JWT claim name for "subject"). Anything else needed about the
    user (email, name) should be looked up from the DB when needed, not
    stuffed into the token -- tokens can't be revoked or updated once
    issued, so keeping them minimal avoids serving stale data from an old
    token for the next 24 hours.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[int]:
    """Returns the user_id encoded in a valid, unexpired token, or None if invalid/expired."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str = payload.get("sub")
        if user_id_str is None:
            return None
        return int(user_id_str)
    except (JWTError, ValueError):
        return None