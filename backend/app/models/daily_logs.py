from datetime import date as date_type, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.session import Base
#from backend.app.models.users import User


class DailyLog(Base):
    """
    One row per user per day. compliance_score is STORED (not recomputed
    on every dashboard read) but always calculated at write-time against
    that user's currently active plan_metrics targets -- never a hardcoded
    number. If targets change later, past logs keep the score they were
    actually scored against at the time, which is correct historical
    behavior, not a bug to "fix" by recalculating old rows.
    """

    __tablename__ = "daily_logs"
    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_user_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[date_type] = mapped_column(Date, nullable=False)

    weight_kg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    calories: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    protein_g: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    carbs_g: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    fat_g: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    steps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sleep_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)
    compliance_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship()