"""
Signup, login, logout, and "who am I" -- email+password only for now.
Google OAuth is a separate, later addition (Stage 3 continues after this).
"""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import COOKIE_NAME, get_current_user
from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.users import User
from app.schemas.auth import LoginRequest, SignupRequest, UserPublic

router = APIRouter()

# secure=True means the cookie is only ever sent over HTTPS. In local dev
# you're on plain http://localhost, so this is tied to ENVIRONMENT --
# flip to True automatically once ENVIRONMENT=production on the real VPS,
# no code change needed at deploy time.
COOKIE_SECURE = settings.ENVIRONMENT != "development"


def _set_auth_cookie(response: Response, user_id: int) -> None:
    token = create_access_token(user_id)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,          # JavaScript can never read this cookie -- the core XSS protection
        secure=COOKIE_SECURE,
        samesite="lax",         # sent on normal navigation/API calls from your own frontend, blocked cross-site
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )


@router.post("/signup", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, response: Response, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = User(
        email=payload.email,
        name=payload.name,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Log the user in immediately on signup -- no separate "please log in
    # now" step, matches how most consumer apps behave.
    _set_auth_cookie(response, user.id)

    return user


@router.post("/login", response_model=UserPublic)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    # Same error for "no such user" and "wrong password" -- revealing which
    # one is true lets an attacker enumerate valid emails on the platform.
    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password"
    )

    if user is None or user.hashed_password is None:
        raise invalid_credentials
    if not verify_password(payload.password, user.hashed_password):
        raise invalid_credentials

    _set_auth_cookie(response, user.id)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    response.delete_cookie(key=COOKIE_NAME, path="/")


@router.get("/me", response_model=UserPublic)
def read_current_user(current_user: User = Depends(get_current_user)):
    """
    Proves the whole chain works: cookie -> decode -> DB lookup -> real user
    returned. This is also the pattern every future protected route follows.
    """
    return current_user