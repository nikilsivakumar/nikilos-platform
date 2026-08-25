"""
Shared FastAPI dependencies. get_current_user is the bridge between
"a request came in with a cookie" and "here is the real User row" --
every protected route depends on this rather than reading the cookie
itself, so there's exactly one place that knows how auth actually works.
"""

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.users import User

COOKIE_NAME = "access_token"


def get_current_user(
    access_token: str | None = Cookie(default=None, alias=COOKIE_NAME),
    db: Session = Depends(get_db),
) -> User:
    """
    Reads the access_token cookie, decodes it, and loads the matching User.
    Raises 401 if the cookie is missing, invalid, expired, or points at a
    user that no longer exists -- any of these mean "not logged in", and a
    route should never have to distinguish between those cases itself.
    """
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
    )

    if access_token is None:
        raise credentials_error

    user_id = decode_access_token(access_token)
    if user_id is None:
        raise credentials_error

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_error

    return user