from datetime import date as date_type, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
#from backend.app.models.exercises import ExerciseCatalog


class WorkoutSession(Base):
    """
    routine_id is nullable -- a logged session doesn't have to come from a
    routine (free-form logging is allowed). started_at/ended_at are what
    the session-duration timer is built from -- no separate timer table needed.
    """

    __tablename__ = "workout_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    routine_id: Mapped[Optional[int]] = mapped_column(ForeignKey("routines.id"), nullable=True)
    date: Mapped[date_type] = mapped_column(Date, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    sets: Mapped[list["WorkoutSet"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class WorkoutSet(Base):
    """
    estimated_1rm is calculated at write-time using the Epley formula
    (weight * (1 + reps/30)) for exercises where category == "loaded" --
    stored here rather than recalculated on every read, same reasoning as
    daily_logs.compliance_score.
    """

    __tablename__ = "workout_sets"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("workout_sessions.id", ondelete="CASCADE"), nullable=False)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercise_catalog.id"), nullable=False)

    set_index: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_kg: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    reps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    estimated_1rm: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)

    session: Mapped["WorkoutSession"] = relationship(back_populates="sets")
    exercise: Mapped["ExerciseCatalog"] = relationship()