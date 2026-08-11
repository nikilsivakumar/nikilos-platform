import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.session import Base


class ExperienceLevel(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class ClientIntro(Base):
    """
    What a coach can see about someone who has requested coaching but not
    yet been accepted (CoachClient.status == 'pending'). Deliberately a
    SEPARATE table from daily_logs/workout_sessions/etc, not just a "show
    partial fields" rule applied to those tables at query time — keeping
    it separate means there's no code path anywhere that queries a
    pending requester's real logs and then just trims the response. The
    permission-check code (next step) grants access to THIS table for
    pending relationships and nothing else.
    """

    __tablename__ = "client_intro"

    id: Mapped[int] = mapped_column(primary_key=True)

    # One intro per coach_client relationship. Deleting the relationship
    # (e.g. a withdrawn request) deletes the intro with it.
    coach_client_id: Mapped[int] = mapped_column(
        ForeignKey("coach_clients.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    goals_text: Mapped[str] = mapped_column(Text, nullable=False)
    experience_level: Mapped[ExperienceLevel] = mapped_column(
        Enum(ExperienceLevel, name="experience_level"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    coach_client: Mapped["CoachClient"] = relationship(back_populates="intro")