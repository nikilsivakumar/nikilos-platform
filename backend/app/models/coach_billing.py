import enum
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Enum, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.session import Base


class BillingTier(str, enum.Enum):
    free = "free"
    paid = "paid"


class CoachBilling(Base):
    """
    One row per coach, tracking their plan tier and slot allowance.

    This table only defines the RULE (how many free slots, what overage
    costs). It does NOT enforce anything by itself — enforcement happens in
    application code at the moment a CoachClient row transitions from
    'pending' to 'active' (the accept-client endpoint, not yet built):
    that endpoint must count the coach's current active CoachClient rows
    and compare against included_slots before allowing another accept.

    This table does NOT solve "one person creates two coach accounts to
    get 15 free slots twice" — that's an identity/fraud problem, not a
    schema problem, and is intentionally left unsolved here. See
    docs/DOMAIN_MODEL.md billing notes for why, and what a real fix would
    require (payment-method fingerprinting, admin-side pattern detection).
    The users.phone_number unique constraint added alongside this table is
    a cheap partial deterrent, not a complete fix.
    """

    __tablename__ = "coach_billing"

    id: Mapped[int] = mapped_column(primary_key=True)

    # One billing row per coach. FK to users.id (not coach_profiles.id) so
    # this table only ever makes sense for a user who is, in fact, a coach —
    # enforced by application logic when this row is created, not by the DB.
    coach_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    plan_tier: Mapped[BillingTier] = mapped_column(
        Enum(BillingTier, name="billing_tier"),
        default=BillingTier.free,
        nullable=False,
    )

    # How many ACTIVE clients this coach can have before hitting overage.
    # Stored per-coach (not a global constant) so a promo or negotiated
    # deal can override it later without a schema change.
    included_slots: Mapped[int] = mapped_column(Integer, default=15, nullable=False)

    # Price charged per client beyond included_slots. Nullable because a
    # free-tier coach who has never gone over doesn't need a price set yet.
    price_per_extra_client: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    coach: Mapped["User"] = relationship()