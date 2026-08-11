from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.session import Base


class User(Base):
    """
    One row per person. This is the ONLY table auth touches.
    There is no 'role' column here on purpose — see docs/DOMAIN_MODEL.md.
    Whether someone is an individual, coach, or client is derived from
    whether they have a CoachProfile and/or rows in CoachClient, not
    stored as a fixed type on this table.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    # Nullable because a user who signs up via Google OAuth has no password.
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Nullable because a user who signs up via email/password has no Google id.
    google_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # One user has at most one coach_profile (they become a coach by having one).
    coach_profile: Mapped[Optional["CoachProfile"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    # Relationships to CoachClient from both sides — a user can appear as
    # a coach in some rows and as a client in others (e.g. a coach who also
    # trains under someone else, or just logs their own workouts).
    clients: Mapped[list["CoachClient"]] = relationship(
        back_populates="coach",
        foreign_keys="CoachClient.coach_id",
        cascade="all, delete-orphan",
    )
    coaching_relationships: Mapped[list["CoachClient"]] = relationship(
        back_populates="client",
        foreign_keys="CoachClient.client_id",
        cascade="all, delete-orphan",
    )