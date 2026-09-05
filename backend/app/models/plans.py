from datetime import date as date_type, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.session import Base


class Plan(Base):
    """
    owner_id = whose plan this is. created_by = who made it (self, or a
    coach). Self-made plans have owner_id == created_by -- same table,
    same shape, no separate "self plan" vs "coach plan" type, matching
    the "one person, layered capabilities" principle from DOMAIN_MODEL.md.
    """

    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    start_date: Mapped[Optional[date_type]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date_type]] = mapped_column(Date, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner: Mapped["User"] = relationship(foreign_keys=[owner_id])
    metrics: Mapped[Optional["PlanMetrics"]] = relationship(back_populates="plan", uselist=False, cascade="all, delete-orphan")


class PlanMetrics(Base):
    """
    One targets row per plan -- calorie/protein/step/sleep targets that
    daily_logs.compliance_score gets scored against. Kept as its own table
    (not columns on plans) per the original "relational, never JSON"
    principle -- makes it trivial to add a new target type later without
    touching the plans table at all.
    """

    __tablename__ = "plan_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id", ondelete="CASCADE"), unique=True, nullable=False)

    calorie_target: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    protein_target: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    step_target: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sleep_target: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)

    plan: Mapped["Plan"] = relationship(back_populates="metrics")