from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, users

app = FastAPI(title="NikilOS Platform API", version="0.1.0")

# Loosened for local dev only -- tighten allow_origins before any real deployment.
# allow_credentials=True is required for cookie-based auth to work across
# the frontend/backend origin split (React on :3000, API on :8000).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])


@app.get("/health")
def health():
    return {"status": "ok"}