"""
CRUD for plans + plan_metrics. Same require_access pattern as every other
data route -- OWN or COACH_FULL, nothing new here.

The one piece of real logic: _deactivate_other_active_plans runs BEFORE
creating or activating a plan, so the database's partial unique index
(see app/models/plans.py) never actually gets a chance to reject anything
in normal use -- it's a safety net, not the primary mechanism.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.permissions import AccessLevel, require_access
from app.db.session import get_db
from app.models.plans import Plan, PlanMetrics
from app.models.users import User
from app.schemas.plans import PlanCreate, PlanPublic, PlanUpdate

router = APIRouter()


def _deactivate_other_active_plans(db: Session, owner_id: int, exclude_plan_id: int | None = None) -> None:
    query = db.query(Plan).filter(Plan.owner_id == owner_id, Plan.is_active == True)  # noqa: E712
    if exclude_plan_id is not None:
        query = query.filter(Plan.id != exclude_plan_id)
    query.update({"is_active": False})


def _upsert_metrics(db: Session, plan: Plan, metrics_data) -> None:
    if metrics_data is None:
        return
    if plan.metrics is None:
        plan.metrics = PlanMetrics(plan_id=plan.id)
        db.add(plan.metrics)
    plan.metrics.calorie_target = metrics_data.calorie_target
    plan.metrics.protein_target = metrics_data.protein_target
    plan.metrics.step_target = metrics_data.step_target
    plan.metrics.sleep_target = metrics_data.sleep_target


@router.post("/{user_id}", response_model=PlanPublic, status_code=status.HTTP_201_CREATED)
def create_plan(
    user_id: int,
    payload: PlanCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_access(db, current_user.id, user_id, allowed={AccessLevel.OWN, AccessLevel.COACH_FULL})

    if payload.is_active:
        _deactivate_other_active_plans(db, owner_id=user_id)

    plan = Plan(
        owner_id=user_id,
        created_by=current_user.id,
        name=payload.name,
        is_active=payload.is_active,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )
    db.add(plan)
    db.flush()  # assigns plan.id without committing yet, needed for metrics FK below

    _upsert_metrics(db, plan, payload.metrics)

    db.commit()
    db.refresh(plan)
    return plan


@router.get("/{user_id}", response_model=list[PlanPublic])
def list_plans(
    user_id: int,
    active_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_access(db, current_user.id, user_id, allowed={AccessLevel.OWN, AccessLevel.COACH_FULL})

    query = db.query(Plan).filter(Plan.owner_id == user_id)
    if active_only:
        query = query.filter(Plan.is_active == True)  # noqa: E712

    return query.order_by(Plan.created_at.desc()).all()


@router.patch("/{user_id}/{plan_id}", response_model=PlanPublic)
def update_plan(
    user_id: int,
    plan_id: int,
    payload: PlanUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_access(db, current_user.id, user_id, allowed={AccessLevel.OWN, AccessLevel.COACH_FULL})

    plan = db.query(Plan).filter(Plan.id == plan_id, Plan.owner_id == user_id).first()
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    if payload.is_active is True and not plan.is_active:
        _deactivate_other_active_plans(db, owner_id=user_id, exclude_plan_id=plan.id)

    if payload.name is not None:
        plan.name = payload.name
    if payload.is_active is not None:
        plan.is_active = payload.is_active
    if payload.start_date is not None:
        plan.start_date = payload.start_date
    if payload.end_date is not None:
        plan.end_date = payload.end_date

    _upsert_metrics(db, plan, payload.metrics)

    db.commit()
    db.refresh(plan)
    return plan


@router.delete("/{user_id}/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(
    user_id: int,
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_access(db, current_user.id, user_id, allowed={AccessLevel.OWN, AccessLevel.COACH_FULL})

    plan = db.query(Plan).filter(Plan.id == plan_id, Plan.owner_id == user_id).first()
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    db.delete(plan)
    db.commit()