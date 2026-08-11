from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.session import Base


class CoachProfile(Base):
    """
    Extends a User into a public, browsable coach. Existence of this row
    (not a role flag) is what makes a user a "coach" — see docs/DOMAIN_MODEL.md.
    An individual user browsing coaches only ever sees rows where is_public=True.
    """

    __tablename__ = "coach_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)

    # One-to-one with users: a user has at most one coach_profile.
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    specialties: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Soft cap on active clients — enforced in application logic when
    # accepting a pending request, not a hard DB constraint.
    capacity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Whether this profile shows up when individuals browse coaches.
    # A coach can flip this off without deleting the profile or losing
    # existing client relationships.
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="coach_profile")