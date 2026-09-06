"""
Request/response schemas for daily_logs. Same separation as auth schemas:
these define the API contract, not the DB row shape.
"""

from datetime import date as date_type
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class DailyLogCreate(BaseModel):
    """
    What the client sends to create/update a log. compliance_score is
    NOT accepted here -- it's calculated server-side, never trusted from
    the client. Accepting a client-supplied score would let anyone report
    a perfect compliance score regardless of their actual numbers.
    """
    date: date_type
    weight_kg: Optional[Decimal] = None
    calories: Optional[int] = None
    protein_g: Optional[Decimal] = None
    steps: Optional[int] = None
    sleep_hours: Optional[Decimal] = None


class DailyLogPublic(BaseModel):
    id: int
    user_id: int
    date: date_type
    weight_kg: Optional[Decimal]
    calories: Optional[int]
    protein_g: Optional[Decimal]
    steps: Optional[int]
    sleep_hours: Optional[Decimal]
    compliance_score: Optional[int]

    class Config:
        from_attributes = True