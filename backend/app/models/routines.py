from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.session import Base


class Routine(Base):
    """
    Two kinds of row, distinguished by is_template:
      - is_template=False (normal): created_by and assigned_to are both
        set. Self-made routines have assigned_to == created_by.
      - is_template=True (starter library): created_by and assigned_to
        are both NULL -- belongs to the platform, not a person. Any user
        can use it directly for logging (workout_sessions.routine_id
        points straight at the template's id -- no copy needed for v1).

    template_group ties multiple template routines together into one
    named split, e.g. "PPL" groups three rows named "Push", "Pull", "Legs".
    template_order controls display order within that group (Push=1,
    Pull=2, Legs=3). Both are NULL for non-template routines -- they only
    mean something in the context of the starter library.
    """

    __tablename__ = "routines"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    assigned_to: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    is_template: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    template_group: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    template_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    exercises: Mapped[list["RoutineExercise"]] = relationship(
        back_populates="routine", cascade="all, delete-orphan", order_by="RoutineExercise.order_index"
    )


class RoutineExercise(Base):
    __tablename__ = "routine_exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    routine_id: Mapped[int] = mapped_column(ForeignKey("routines.id", ondelete="CASCADE"), nullable=False)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercise_catalog.id"), nullable=False)

    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    target_sets: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    target_reps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    target_rest_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    superset_group: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    routine: Mapped["Routine"] = relationship(back_populates="exercises")
    exercise: Mapped["ExerciseCatalog"] = relationship()