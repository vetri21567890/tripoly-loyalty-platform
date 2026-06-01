import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin


class ReferralRewardRule(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "referral_reward_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    qualified_coins: Mapped[int] = mapped_column(Integer, nullable=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), default="active")


class BookingBonusBracket(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "booking_bonus_brackets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    min_amount_inr: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    max_amount_inr: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    coins_awarded: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active")


class BirthdayBonusRule(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "birthday_bonus_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    coins_awarded: Mapped[int] = mapped_column(Integer, nullable=False)
    award_frequency: Mapped[str] = mapped_column(String(32), default="yearly")
    status: Mapped[str] = mapped_column(String(32), default="active")
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
