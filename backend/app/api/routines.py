"""
CRUD for personal routines, plus a separate public read-only endpoint for
the template library. Templates are NOT created through this API at all
-- they're seeded directly (is_template=True, created_by/assigned_to
NULL), so there's no user-facing "create a template" route here on purpose.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.permissions import AccessLevel, require_access
from app.db.session import get_db
from app.models.exercises import ExerciseCatalog
from app.models.routines import Routine, RoutineExercise
from app.models.users import User
from app.schemas.routines import RoutineCreate, RoutineExercisePublic, RoutinePublic, RoutineUpdate

router = APIRouter()


def _to_public(routine: Routine) -> RoutinePublic:
    exercises = [
        RoutineExercisePublic(
            id=re.id,
            exercise_id=re.exercise_id,
            exercise_name=re.exercise.name,
            order_index=re.order_index,
            target_sets=re.target_sets,
            target_reps=re.target_reps,
            target_rest_seconds=re.target_rest_seconds,
            superset_group=re.superset_group,
        )
        for re in sorted(routine.exercises, key=lambda e: e.order_index)
    ]
    return RoutinePublic(
        id=routine.id, created_by=routine.created_by, assigned_to=routine.assigned_to,
        is_template=routine.is_template, template_group=routine.template_group,
        template_order=routine.template_order, name=routine.name, exercises=exercises,
    )


def _replace_exercises(db: Session, routine: Routine, exercises_data) -> None:
    for existing in list(routine.exercises):
        db.delete(existing)
    db.flush()
    for ex_data in exercises_data:
        exercise = db.query(ExerciseCatalog).filter(ExerciseCatalog.id == ex_data.exercise_id).first()
        if exercise is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"exercise_id {ex_data.exercise_id} does not exist in exercise_catalog",
            )
        db.add(RoutineExercise(
            routine_id=routine.id, exercise_id=ex_data.exercise_id, order_index=ex_data.order_index,
            target_sets=ex_data.target_sets, target_reps=ex_data.target_reps,
            target_rest_seconds=ex_data.target_rest_seconds, superset_group=ex_data.superset_group,
        ))


@router.get("/templates", response_model=list[RoutinePublic])
def list_templates(
    current_user: User = Depends(get_current_user),  # must be logged in, but no ownership check -- public to all users
    db: Session = Depends(get_db),
):
    templates = (
        db.query(Routine)
        .filter(Routine.is_template == True)  # noqa: E712
        .order_by(Routine.template_group, Routine.template_order)
        .all()
    )
    return [_to_public(t) for t in templates]


@router.post("/{user_id}", response_model=RoutinePublic, status_code=status.HTTP_201_CREATED)
def create_routine(
    user_id: int,
    payload: RoutineCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """user_id is who the routine is FOR (assigned_to) -- a coach can create one for their active client."""
    require_access(db, current_user.id, user_id, allowed={AccessLevel.OWN, AccessLevel.COACH_FULL})

    routine = Routine(created_by=current_user.id, assigned_to=user_id, is_template=False, name=payload.name)
    db.add(routine)
    db.flush()

    _replace_exercises(db, routine, payload.exercises)

    db.commit()
    db.refresh(routine)
    return _to_public(routine)


@router.get("/{user_id}", response_model=list[RoutinePublic])
def list_routines(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Personal routines only -- use GET /routines/templates separately for the shared library."""
    require_access(db, current_user.id, user_id, allowed={AccessLevel.OWN, AccessLevel.COACH_FULL})

    routines = db.query(Routine).filter(Routine.assigned_to == user_id).order_by(Routine.created_at.desc()).all()
    return [_to_public(r) for r in routines]


@router.get("/{user_id}/{routine_id}", response_model=RoutinePublic)
def get_routine(
    user_id: int,
    routine_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    routine = db.query(Routine).filter(Routine.id == routine_id).first()
    if routine is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Routine not found")

    if not routine.is_template:
        require_access(db, current_user.id, user_id, allowed={AccessLevel.OWN, AccessLevel.COACH_FULL})
        if routine.assigned_to != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Routine not found")

    return _to_public(routine)


@router.patch("/{user_id}/{routine_id}", response_model=RoutinePublic)
def update_routine(
    user_id: int,
    routine_id: int,
    payload: RoutineUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_access(db, current_user.id, user_id, allowed={AccessLevel.OWN, AccessLevel.COACH_FULL})

    routine = db.query(Routine).filter(Routine.id == routine_id, Routine.assigned_to == user_id).first()
    if routine is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Routine not found")

    if payload.name is not None:
        routine.name = payload.name
    if payload.exercises is not None:
        _replace_exercises(db, routine, payload.exercises)

    db.commit()
    db.refresh(routine)
    return _to_public(routine)


@router.delete("/{user_id}/{routine_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_routine(
    user_id: int,
    routine_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_access(db, current_user.id, user_id, allowed={AccessLevel.OWN, AccessLevel.COACH_FULL})

    routine = db.query(Routine).filter(Routine.id == routine_id, Routine.assigned_to == user_id).first()
    if routine is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Routine not found")

    db.delete(routine)
    db.commit()