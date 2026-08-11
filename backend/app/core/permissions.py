"""
The single source of truth for "who can see whose data" across the whole
platform. Every route that touches a user's data — daily_logs, plans,
workout_sessions, etc, once those exist — must go through get_access_level
(or the require_access wrapper below) rather than writing its own check.

Deliberately built and tested as plain Python functions here, independent
of FastAPI or auth. Auth doesn't exist yet — once it does, a thin FastAPI
dependency will call get_access_level with the authenticated user's id.
Keeping the actual rule-checking logic separate from that wiring means it
can be tested directly (see tests/test_permissions.py) without needing a
real HTTP request or a JWT.
"""

import enum

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.coach_clients import CoachClient, CoachClientStatus


class AccessLevel(str, enum.Enum):
    OWN = "own"                        # requester IS the target user — full access
    COACH_FULL = "coach_full"          # active coach_clients row — full access
    COACH_INTRO_ONLY = "coach_intro_only"  # pending row — client_intro fields only
    NONE = "none"                      # no relationship, or inactive — no access


def get_access_level(db: Session, requester_id: int, target_user_id: int) -> AccessLevel:
    """
    Looks up exactly one thing: does requester_id have any standing to see
    target_user_id's data, and how much.

    Rules (see docs/DOMAIN_MODEL.md "RBAC — permission matrix"):
      - A user always has OWN access to their own data.
      - A coach with an ACTIVE coach_clients row for this target gets FULL access.
      - A coach with a PENDING row gets INTRO_ONLY (client_intro table only).
      - Anything else (no row, or INACTIVE row) is NONE.

    Order matters: OWN is checked before querying coach_clients at all —
    a user is never dependent on a relationship row to see their own data.
    """
    if requester_id == target_user_id:
        return AccessLevel.OWN

    row = (
        db.query(CoachClient)
        .filter(
            CoachClient.coach_id == requester_id,
            CoachClient.client_id == target_user_id,
        )
        .first()
    )

    if row is None:
        return AccessLevel.NONE
    if row.status == CoachClientStatus.active:
        return AccessLevel.COACH_FULL
    if row.status == CoachClientStatus.pending:
        return AccessLevel.COACH_INTRO_ONLY
    return AccessLevel.NONE  # inactive


def require_access(
    db: Session,
    requester_id: int,
    target_user_id: int,
    allowed: set[AccessLevel],
) -> AccessLevel:
    """
    Route-facing helper: checks access and raises HTTP 403 if the level
    achieved isn't in the allowed set for that endpoint. Returns the level
    on success so a route can still branch on OWN vs COACH_FULL if needed.

    Example (once auth + a real route exist):
        level = require_access(
            db, current_user.id, target_user_id,
            allowed={AccessLevel.OWN, AccessLevel.COACH_FULL},
        )
    A route serving full daily_logs would pass that `allowed` set — note
    COACH_INTRO_ONLY is deliberately excluded, since a pending coach must
    not reach full log data through this same endpoint.
    """
    level = get_access_level(db, requester_id, target_user_id)
    if level not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return level