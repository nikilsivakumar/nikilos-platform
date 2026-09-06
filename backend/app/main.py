from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api import auth, users
from app.core.config import settings

from app.api import auth, users, daily_logs, body_measurements, plans,routines

app = FastAPI(title="NikilOS Platform API", version="0.1.0")

# Loosened for local dev only -- tighten allow_origins before any real deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Required by authlib's Google OAuth flow: it stores a short-lived state
# value in a server-side session between the /google/login redirect and
# the /google/callback that follows, to prevent CSRF on the OAuth handshake.
# This is separate from your own JWT auth cookie -- different mechanism,
# different purpose, both can coexist.
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(daily_logs.router, prefix="/daily-logs", tags=["daily-logs"])
app.include_router(body_measurements.router, prefix="/body-measurements", tags=["body-measurements"])
app.include_router(plans.router, prefix="/plans", tags=["plans"])
app.include_router(routines.router, prefix="/routines", tags=["routines"])

@app.get("/health")
def health():
    return {"status": "ok"}