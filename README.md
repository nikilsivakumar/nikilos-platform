# NikilOS Platform

Multi-user fitness coaching operating system. Individuals log their own training with or without a coach; coaches manage clients through a permission boundary that keeps every client's data private from every other client and from other coaches.

This is a from-scratch rebuild (2026-08). Prior SQLite/Streamlit and unsaved FastAPI prototypes are retired — see `docs/DOMAIN_MODEL.md` for why, and for the locked data model going forward.

## Stack

- **Backend**: FastAPI + PostgreSQL + SQLAlchemy + Alembic
- **Frontend** (later): React (coach/individual web dashboard), React Native/Expo (client mobile app)
- **Hosting**: self-managed VPS (Postgres included)

## Repo structure

```
nikilos-platform/
├── docs/
│   └── DOMAIN_MODEL.md      # locked entities, relationships, RBAC matrix
├── backend/
│   ├── app/
│   │   ├── core/            # settings, config
│   │   ├── db/              # engine, session, declarative base
│   │   ├── models/          # SQLAlchemy models (not yet written — next step)
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── api/             # route modules
│   │   └── main.py          # FastAPI app entrypoint
│   ├── alembic/              # migrations
│   ├── requirements.txt
│   └── .env.example
└── README.md
```

## Local setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # fill in your local Postgres credentials
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/health` — should return `{"status": "ok"}`. That's the only working endpoint right now; everything else is scaffold until the domain model is implemented.

## Status

See `docs/DOMAIN_MODEL.md` for the current build phase and what's locked vs. next.
