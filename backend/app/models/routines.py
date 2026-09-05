from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.session import Base


class Routine(Base):
    """
    Self-made routines have assigned_to == created_by -- same table,
    same shape, whether you made it for yourself or your coach assigned
    it to you. No separate "template" vs "assigned" type.
    """

    __tablename__ = "routines"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    assigned_to: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    exercises: Mapped[list["RoutineExercise"]] = relationship(
        back_populates="routine", cascade="all, delete-orphan", order_by="RoutineExercise.order_index"
    )


class RoutineExercise(Base):
    """
    One exercise slot within a routine. target_rest_seconds and
    superset_group added 2026-08-25 (see FEATURE_BACKLOG.md Approved for
    Stage 4) -- both nullable, so existing rows are unaffected if either
    feature isn't used for a given exercise.
    """

    __tablename__ = "routine_exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    routine_id: Mapped[int] = mapped_column(ForeignKey("routines.id", ondelete="CASCADE"), nullable=False)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercise_catalog.id"), nullable=False)

    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    target_sets: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    target_reps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Rest timer: countdown shown after logging a set of this exercise.
    target_rest_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Supersets: exercises sharing a non-null value in the same routine
    # are grouped together by the frontend.
    superset_group: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    routine: Mapped["Routine"] = relationship(back_populates="exercises")
    exercise: Mapped["ExerciseCatalog"] = relationship()