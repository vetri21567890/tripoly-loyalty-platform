import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import LoyaltyTierCode
from app.models.mixins import SoftDeleteMixin, TimestampMixin


class LoyaltyTier(Base):
    __tablename__ = "loyalty_tiers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[LoyaltyTierCode] = mapped_column(
        ENUM(LoyaltyTierCode, name="loyalty_tier_code", create_type=True), unique=True
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    min_lifetime_coins: Mapped[int] = mapped_column(Integer, nullable=False)
    max_lifetime_coins: Mapped[int | None] = mapped_column(Integer)
    perks_jsonb: Mapped[dict] = mapped_column(JSONB, default=dict)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)


class CustomerCurrentTier(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "customer_current_tier"

    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), primary_key=True
    )
    tier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("loyalty_tiers.id"))
    lifetime_coins_at_set: Mapped[int] = mapped_column(Integer, nullable=False)
    set_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CustomerTierHistory(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "customer_tier_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"))
    tier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("loyalty_tiers.id"))
    lifetime_coins_at_upgrade: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    achieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
