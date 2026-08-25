"""
First real route protected by require_access instead of a test fixture --
this is the payoff of building permissions.py before auth existed. The
logic itself is unchanged from what the 11 tests already proved; only the
source of current_user is new (a real cookie instead of a hardcoded id).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.permissions import AccessLevel, require_access
from app.db.session import get_db
from app.models.users import User
from app.schemas.auth import UserPublic

router = APIRouter()


@router.get("/{user_id}", response_model=UserPublic)
def get_user_profile(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns a user's basic profile. Allowed if you're looking at your own
    profile (OWN) or you're their coach with an active relationship
    (COACH_FULL) -- deliberately excludes COACH_INTRO_ONLY, since a pending
    coach shouldn't see even basic profile info through this route yet
    (that's what client_intro is for, once its endpoint exists).
    """
    require_access(
        db, current_user.id, user_id,
        allowed={AccessLevel.OWN, AccessLevel.COACH_FULL},
    )
    target_user = db.query(User).filter(User.id == user_id).first()
    return target_user