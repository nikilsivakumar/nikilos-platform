from datetime import date as date_type
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class PlanMetricsData(BaseModel):
    calorie_target: Optional[int] = None
    protein_target: Optional[Decimal] = None
    step_target: Optional[int] = None
    sleep_target: Optional[Decimal] = None


class PlanCreate(BaseModel):
    name: str
    is_active: bool = True
    start_date: Optional[date_type] = None
    end_date: Optional[date_type] = None
    metrics: Optional[PlanMetricsData] = None


class PlanUpdate(BaseModel):
    """All fields optional -- only what's provided gets changed."""
    name: Optional[str] = None
    is_active: Optional[bool] = None
    start_date: Optional[date_type] = None
    end_date: Optional[date_type] = None
    metrics: Optional[PlanMetricsData] = None


class PlanMetricsPublic(BaseModel):
    calorie_target: Optional[int]
    protein_target: Optional[Decimal]
    step_target: Optional[int]
    sleep_target: Optional[Decimal]

    class Config:
        from_attributes = True


class PlanPublic(BaseModel):
    id: int
    owner_id: int
    created_by: int
    name: str
    is_active: bool
    start_date: Optional[date_type]
    end_date: Optional[date_type]
    metrics: Optional[PlanMetricsPublic]

    class Config:
        from_attributes = True