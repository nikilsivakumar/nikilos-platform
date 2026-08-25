"""
Signup, login, logout, "who am I" (email+password), and Google OAuth.

Google OAuth flow, in plain terms:
  1. User hits GET /auth/google/login -> we redirect them to Google's
     consent screen.
  2. User approves on Google's site (not ours -- we never see their
     Google password).
  3. Google redirects back to GET /auth/google/callback with a temporary
     code. We exchange that code for the user's verified email/name, then
     run the SAME account-linking logic used by nothing else in this file
     (see app/core/google_auth.py) to find-or-create the matching local
     User row, and issue the SAME cookie-based token as normal login.

After step 3, a Google-authenticated user is indistinguishable from a
password-authenticated one anywhere else in the app -- get_current_user
doesn't know or care how you logged in.
"""

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import COOKIE_NAME, get_current_user
from app.core.config import settings
from app.core.google_auth import get_or_create_user_from_google
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.users import User
from app.schemas.auth import LoginRequest, SignupRequest, UserPublic

router = APIRouter()

COOKIE_SECURE = settings.ENVIRONMENT != "development"

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


def _set_auth_cookie(response: Response, user_id: int) -> None:
    token = create_access_token(user_id)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
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

    _set_auth_cookie(response, user.id)
    return user


@router.post("/login", response_model=UserPublic)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

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
    return current_user


@router.get("/google/login")
async def google_login(request: Request):
    """Kicks off the flow -- redirects the browser to Google's consent screen."""
    return await oauth.google.authorize_redirect(request, settings.GOOGLE_REDIRECT_URI)


@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """
    Google redirects here after the user approves. We exchange the code
    for their verified profile, resolve/create the local User via
    get_or_create_user_from_google, then log them in exactly like any
    other user -- same cookie, same downstream behavior.
    """
    token = await oauth.google.authorize_access_token(request)
    userinfo = token.get("userinfo")
    if userinfo is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google did not return user info")

    google_id = userinfo["sub"]
    email = userinfo["email"]
    name = userinfo.get("name", email.split("@")[0])

    user = get_or_create_user_from_google(db, google_id=google_id, email=email, name=name)

    # Redirect to the frontend after login. Placeholder target until the
    # real frontend exists -- update this once Stage 11 (frontend) starts.
    response = RedirectResponse(url="http://localhost:3000/dashboard")
    _set_auth_cookie(response, user.id)
    return response