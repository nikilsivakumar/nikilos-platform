from datetime import date as date_type
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class BodyMeasurementCreate(BaseModel):
    date: date_type
    height_cm: Optional[Decimal] = None
    neck_cm: Optional[Decimal] = None
    shoulder_cm: Optional[Decimal] = None
    chest_cm: Optional[Decimal] = None
    waist_cm: Optional[Decimal] = None
    hip_cm: Optional[Decimal] = None
    bicep_cm: Optional[Decimal] = None
    thigh_cm: Optional[Decimal] = None
    calf_cm: Optional[Decimal] = None
    body_fat_pct_manual: Optional[Decimal] = None


class BodyMeasurementPublic(BaseModel):
    id: int
    user_id: int
    date: date_type
    height_cm: Optional[Decimal]
    neck_cm: Optional[Decimal]
    shoulder_cm: Optional[Decimal]
    chest_cm: Optional[Decimal]
    waist_cm: Optional[Decimal]
    hip_cm: Optional[Decimal]
    bicep_cm: Optional[Decimal]
    thigh_cm: Optional[Decimal]
    calf_cm: Optional[Decimal]
    body_fat_pct_manual: Optional[Decimal]
    # Calculated fresh on every read, never stored -- see app/core/body_fat.py
    estimated_body_fat_pct: Optional[float] = None

    class Config:
        from_attributes = True


class BiologicalSexUpdate(BaseModel):
    biological_sex: str  # "male" or "female" -- validated against the enum in the route