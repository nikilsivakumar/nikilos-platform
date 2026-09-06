"""
CRUD for body_measurements, plus a small profile-update endpoint for
biological_sex -- without it, estimated_body_fat_pct can never calculate
(see app/core/body_fat.py), so it has to live somewhere reachable.
"""

from datetime import date as date_type
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.body_fat import calculate_navy_body_fat_pct
from app.core.permissions import AccessLevel, require_access
from app.db.session import get_db
from app.models.body_measurements import BodyMeasurement
from app.models.users import BiologicalSex, User
from app.schemas.body_measurements import BiologicalSexUpdate, BodyMeasurementCreate, BodyMeasurementPublic

router = APIRouter()


def _to_public(measurement: BodyMeasurement, user: User) -> BodyMeasurementPublic:
    """
    Attaches the calculated (never stored) body fat estimate to the
    response. Prefers body_fat_pct_manual (a real scan/scale reading) when
    present -- the Navy-method estimate is a fallback, not an override.
    """
    public = BodyMeasurementPublic.model_validate(measurement)
    if measurement.body_fat_pct_manual is not None:
        public.estimated_body_fat_pct = float(measurement.body_fat_pct_manual)
    else:
        public.estimated_body_fat_pct = calculate_navy_body_fat_pct(
            sex=user.biological_sex,
            height_cm=measurement.height_cm,
            neck_cm=measurement.neck_cm,
            waist_cm=measurement.waist_cm,
            hip_cm=measurement.hip_cm,
        )
    return public


@router.post("/{user_id}", response_model=BodyMeasurementPublic, status_code=status.HTTP_201_CREATED)
def create_or_update_measurement(
    user_id: int,
    payload: BodyMeasurementCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_access(db, current_user.id, user_id, allowed={AccessLevel.OWN, AccessLevel.COACH_FULL})

    measurement = (
        db.query(BodyMeasurement)
        .filter(BodyMeasurement.user_id == user_id, BodyMeasurement.date == payload.date)
        .first()
    )
    if measurement is None:
        measurement = BodyMeasurement(user_id=user_id, date=payload.date)
        db.add(measurement)

    for field in [
        "height_cm", "neck_cm", "shoulder_cm", "chest_cm", "waist_cm",
        "hip_cm", "bicep_cm", "thigh_cm", "calf_cm", "body_fat_pct_manual",
    ]:
        setattr(measurement, field, getattr(payload, field))

    db.commit()
    db.refresh(measurement)

    target_user = db.query(User).filter(User.id == user_id).first()
    return _to_public(measurement, target_user)


@router.get("/{user_id}", response_model=list[BodyMeasurementPublic])
def list_measurements(
    user_id: int,
    start_date: Optional[date_type] = None,
    end_date: Optional[date_type] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_access(db, current_user.id, user_id, allowed={AccessLevel.OWN, AccessLevel.COACH_FULL})

    query = db.query(BodyMeasurement).filter(BodyMeasurement.user_id == user_id)
    if start_date is not None:
        query = query.filter(BodyMeasurement.date >= start_date)
    if end_date is not None:
        query = query.filter(BodyMeasurement.date <= end_date)

    target_user = db.query(User).filter(User.id == user_id).first()
    return [_to_public(m, target_user) for m in query.order_by(BodyMeasurement.date).all()]


@router.delete("/{user_id}/{measurement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_measurement(
    user_id: int,
    measurement_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_access(db, current_user.id, user_id, allowed={AccessLevel.OWN, AccessLevel.COACH_FULL})

    measurement = (
        db.query(BodyMeasurement)
        .filter(BodyMeasurement.id == measurement_id, BodyMeasurement.user_id == user_id)
        .first()
    )
    if measurement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Measurement not found")

    db.delete(measurement)
    db.commit()


@router.patch("/me/biological-sex", status_code=status.HTTP_204_NO_CONTENT)
def update_biological_sex(
    payload: BiologicalSexUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """No require_access needed -- you can only ever set this on yourself, there's no user_id param at all."""
    try:
        sex = BiologicalSex(payload.biological_sex)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="biological_sex must be 'male' or 'female'")

    current_user.biological_sex = sex
    db.commit()