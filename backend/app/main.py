from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="NikilOS Platform API", version="0.1.0")

# Loosened for local dev only — tighten allow_origins before any real deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    """
    Confirms the app boots and serves requests. Does NOT confirm the database
    is reachable yet — that check gets added once models + a real DB exist.
    """
    return {"status": "ok"}


# Route modules get included here as they're built, e.g.:
# from app.api import auth
# app.include_router(auth.router, prefix="/auth", tags=["auth"])
