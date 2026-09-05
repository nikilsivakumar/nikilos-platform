import enum
from typing import Optional

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class ExerciseCategory(str, enum.Enum):
    """Determines how 1RM gets calculated -- some exercise types can't have a meaningful 1RM at all."""
    loaded = "loaded"                        # barbell/dumbbell -- Epley formula applies
    bodyweight = "bodyweight"                # pull-ups etc -- reps matter, weight is bodyweight
    bodyweight_assisted = "bodyweight_assisted"  # assisted dip machine etc
    no_1rm = "no_1rm"                        # cardio, stretching -- 1RM is meaningless


class MuscleGroup(str, enum.Enum):
    chest = "chest"
    back = "back"
    shoulders = "shoulders"
    biceps = "biceps"
    triceps = "triceps"
    legs = "legs"
    core = "core"
    full_body = "full_body"
    cardio = "cardio"


class ExerciseCatalog(Base):
    """
    Shared reference data -- NOT per-user. Every user picks from the same
    catalog rather than each having their own copy of "Barbell Bench Press".
    primary_muscle_group is a single value (v1 heatmap) -- see
    FEATURE_BACKLOG.md for the multi-muscle join-table upgrade path if
    this ever feels insufficient in practice.
    """

    __tablename__ = "exercise_catalog"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    category: Mapped[ExerciseCategory] = mapped_column(Enum(ExerciseCategory, name="exercise_category"), nullable=False)
    primary_muscle_group: Mapped[Optional[MuscleGroup]] = mapped_column(Enum(MuscleGroup, name="muscle_group"), nullable=True)

    aliases: Mapped[list["ExerciseAlias"]] = relationship(back_populates="exercise", cascade="all, delete-orphan")


class ExerciseAlias(Base):
    """Alternate names mapping to a catalog entry -- e.g. 'BB Bench' -> 'Barbell Bench Press', for import matching."""

    __tablename__ = "exercise_aliases"

    id: Mapped[int] = mapped_column(primary_key=True)
    alias: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercise_catalog.id", ondelete="CASCADE"), nullable=False)

    exercise: Mapped["ExerciseCatalog"] = relationship(back_populates="aliases")