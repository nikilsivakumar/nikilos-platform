from datetime import date as date_type
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.compliance import calculate_compliance_score
from app.core.permissions import AccessLevel, require_access
from app.db.session import get_db
from app.models.daily_logs import DailyLog
from app.models.users import User
from app.schemas.daily_logs import DailyLogCreate, DailyLogPublic

router = APIRouter()


@router.post("/{user_id}", response_model=DailyLogPublic, status_code=status.HTTP_201_CREATED)
def create_or_update_daily_log(
    user_id: int,
    payload: DailyLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_access(db, current_user.id, user_id, allowed={AccessLevel.OWN, AccessLevel.COACH_FULL})

    log = db.query(DailyLog).filter(DailyLog.user_id == user_id, DailyLog.date == payload.date).first()
    if log is None:
        log = DailyLog(user_id=user_id, date=payload.date)
        db.add(log)

    log.weight_kg = payload.weight_kg
    log.calories = payload.calories
    log.protein_g = payload.protein_g
    log.carbs_g = payload.carbs_g
    log.fat_g = payload.fat_g
    log.steps = payload.steps
    log.sleep_hours = payload.sleep_hours
    log.compliance_score = calculate_compliance_score(
        db, user_id, payload.weight_kg, payload.calories, payload.protein_g, payload.steps, payload.sleep_hours
    )

    db.commit()
    db.refresh(log)
    return log


@router.get("/{user_id}", response_model=list[DailyLogPublic])
def list_daily_logs(
    user_id: int,
    start_date: Optional[date_type] = None,
    end_date: Optional[date_type] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_access(db, current_user.id, user_id, allowed={AccessLevel.OWN, AccessLevel.COACH_FULL})

    query = db.query(DailyLog).filter(DailyLog.user_id == user_id)
    if start_date is not None:
        query = query.filter(DailyLog.date >= start_date)
    if end_date is not None:
        query = query.filter(DailyLog.date <= end_date)

    return query.order_by(DailyLog.date).all()


@router.delete("/{user_id}/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_daily_log(
    user_id: int,
    log_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_access(db, current_user.id, user_id, allowed={AccessLevel.OWN, AccessLevel.COACH_FULL})

    log = db.query(DailyLog).filter(DailyLog.id == log_id, DailyLog.user_id == user_id).first()
    if log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log not found")

    db.delete(log)
    db.commit()