"""
Periodic body measurements -- height, circumferences. Deliberately
separate from daily_logs: those are daily behaviors (weight, macros,
steps, sleep); these are occasional snapshots (weekly/monthly at most).
Mixing the two cadences into one table would mean mostly-empty columns
on every daily row.

All measurement fields are nullable -- a user might log only waist+neck
one day and shoulder+chest another. estimated_body_fat_pct is NOT stored
here; it's calculated on read (see app/core/body_fat.py) so improvements
to the formula apply retroactively to old measurements too.
"""

from datetime import date as date_type, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.session import Base


class BodyMeasurement(Base):
    __tablename__ = "body_measurements"
    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_user_measurement_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[date_type] = mapped_column(Date, nullable=False)

    height_cm: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    neck_cm: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    shoulder_cm: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    chest_cm: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    waist_cm: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    hip_cm: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    bicep_cm: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    thigh_cm: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    calf_cm: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)

    # A directly measured/scanned value (smart scale, calipers, DEXA) --
    # more accurate than the Navy-method estimate when available. Dashboard
    # should prefer this over the calculated estimate when both exist.
    body_fat_pct_manual: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship()