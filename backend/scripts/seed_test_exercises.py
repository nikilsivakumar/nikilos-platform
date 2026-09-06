"""
Seeds a handful of exercises for testing routines/workouts against real
data. NOT the real exercise catalog (#13 in the backlog) -- just enough
to unblock testing #11/#12. Safe to re-run: checks by name before
inserting, so it won't create duplicates if run twice.

Run from backend/, venv active:
    python scripts/seed_test_exercises.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.exercises import ExerciseCatalog, ExerciseCategory, MuscleGroup

TEST_EXERCISES = [
    ("Barbell Bench Press", ExerciseCategory.loaded, MuscleGroup.chest),
    ("Barbell Back Squat", ExerciseCategory.loaded, MuscleGroup.legs),
    ("Conventional Deadlift", ExerciseCategory.loaded, MuscleGroup.back),
    ("Overhead Press", ExerciseCategory.loaded, MuscleGroup.shoulders),
    ("Barbell Row", ExerciseCategory.loaded, MuscleGroup.back),
    ("Pull-Up", ExerciseCategory.bodyweight, MuscleGroup.back),
    ("Push-Up", ExerciseCategory.bodyweight, MuscleGroup.chest),
    ("Barbell Curl", ExerciseCategory.loaded, MuscleGroup.biceps),
    ("Triceps Pushdown", ExerciseCategory.loaded, MuscleGroup.triceps),
    ("Plank", ExerciseCategory.no_1rm, MuscleGroup.core),
]


def main():
    db = SessionLocal()
    created = 0
    for name, category, muscle_group in TEST_EXERCISES:
        existing = db.query(ExerciseCatalog).filter(ExerciseCatalog.name == name).first()
        if existing is not None:
            print(f"  skip (exists): {name}")
            continue
        db.add(ExerciseCatalog(name=name, category=category, primary_muscle_group=muscle_group))
        created += 1
        print(f"  created: {name}")
    db.commit()
    db.close()
    print(f"\nDone -- {created} new exercise(s) created.")


if __name__ == "__main__":
    main()