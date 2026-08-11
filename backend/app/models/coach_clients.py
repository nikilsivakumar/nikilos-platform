import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.session import Base


class CoachClientStatus(str, enum.Enum):
    pending = "pending"
    active = "active"
    inactive = "inactive"


class CoachClient(Base):
    """
    THE permission boundary for the entire platform. See docs/DOMAIN_MODEL.md
    "RBAC — permission matrix". Every access check that isn't "is this my own
    data" ultimately comes down to a lookup against this table:

      - status == "active"  -> coach has full access to this client's data
      - status == "pending" -> coach may see client_intro fields ONLY
      - status == "inactive" or no row -> coach has no access at all

    Do not add shortcuts elsewhere that bypass this table. If a new feature
    needs a new kind of access, it should be expressed as a status or a
    related table (like client_intro), not a special case in a route handler.
    """

    __tablename__ = "coach_clients"
    __table_args__ = (
        UniqueConstraint("coach_id", "client_id", name="uq_coach_client_pair"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    coach_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    client_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    status: Mapped[CoachClientStatus] = mapped_column(
        Enum(CoachClientStatus, name="coach_client_status"),
        default=CoachClientStatus.pending,
        nullable=False,
    )

    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    coach: Mapped["User"] = relationship(back_populates="clients", foreign_keys=[coach_id])
    client: Mapped["User"] = relationship(back_populates="coaching_relationships", foreign_keys=[client_id])

    # The basic-intro info a coach can see while this row is still "pending" —
    # goals + experience level only, never full logs (enforced in the
    # permission-check code, not by this relationship existing). One intro
    # per relationship, deleted automatically if the relationship row is.
    intro: Mapped[Optional["ClientIntro"]] = relationship(
        back_populates="coach_client", uselist=False, cascade="all, delete-orphan"
    )

    # NOTE: client_intro (the pending-request goals/experience-level table
    # from docs/DOMAIN_MODEL.md) is not built yet. It gets added as its own
    # migration next, with a relationship added back here at that point —
    # deliberately not stubbed out now so this file only claims what exists.