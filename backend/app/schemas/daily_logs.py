from datetime import date as date_type
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class DailyLogCreate(BaseModel):
    date: date_type
    weight_kg: Optional[Decimal] = None
    calories: Optional[int] = None
    protein_g: Optional[Decimal] = None
    carbs_g: Optional[Decimal] = None
    fat_g: Optional[Decimal] = None
    steps: Optional[int] = None
    sleep_hours: Optional[Decimal] = None


class DailyLogPublic(BaseModel):
    id: int
    user_id: int
    date: date_type
    weight_kg: Optional[Decimal]
    calories: Optional[int]
    protein_g: Optional[Decimal]
    carbs_g: Optional[Decimal]
    fat_g: Optional[Decimal]
    steps: Optional[int]
    sleep_hours: Optional[Decimal]
    compliance_score: Optional[int]

    class Config:
        from_attributes = True