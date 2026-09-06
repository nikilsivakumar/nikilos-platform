from typing import Optional

from pydantic import BaseModel


class RoutineExerciseCreate(BaseModel):
    exercise_id: int
    order_index: int
    target_sets: Optional[int] = None
    target_reps: Optional[int] = None
    target_rest_seconds: Optional[int] = None
    superset_group: Optional[int] = None


class RoutineCreate(BaseModel):
    name: str
    exercises: list[RoutineExerciseCreate] = []


class RoutineUpdate(BaseModel):
    name: Optional[str] = None
    # If provided, REPLACES the entire exercise list (simplest correct
    # behavior for v1 -- avoids diffing logic for reordering/removing).
    exercises: Optional[list[RoutineExerciseCreate]] = None


class RoutineExercisePublic(BaseModel):
    id: int
    exercise_id: int
    exercise_name: str  # filled in manually from the relationship, not a DB column
    order_index: int
    target_sets: Optional[int]
    target_reps: Optional[int]
    target_rest_seconds: Optional[int]
    superset_group: Optional[int]


class RoutinePublic(BaseModel):
    id: int
    created_by: Optional[int]
    assigned_to: Optional[int]
    is_template: bool
    template_group: Optional[str]
    template_order: Optional[int]
    name: str
    exercises: list[RoutineExercisePublic]