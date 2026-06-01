import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import RewardStatus
from app.models.mixins import SoftDeleteMixin, TimestampMixin


class RewardCatalog(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "reward_catalog"
    __table_args__ = (
        CheckConstraint("cost_coins > 0", name="ck_reward_cost"),
        CheckConstraint(
            "(unlimited_inventory = true AND inventory_count IS NULL AND inventory_remaining IS NULL) OR "
            "(unlimited_inventory = false AND inventory_count IS NOT NULL AND inventory_remaining IS NOT NULL)",
            name="ck_reward_inventory",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    reward_type: Mapped[str] = mapped_column(String(64), nullable=False)
    cost_coins: Mapped[int] = mapped_column(Integer, nullable=False)
    unlimited_inventory: Mapped[bool] = mapped_column(Boolean, nullable=False)
    inventory_count: Mapped[int | None] = mapped_column(Integer)
    inventory_remaining: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32), default="active")
    metadata_jsonb: Mapped[dict] = mapped_column(JSONB, default=dict)


class RewardRedemption(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "reward_redemptions"
    __table_args__ = (
        UniqueConstraint("customer_id", "idempotency_key", name="uq_reward_redemption_idempotency"),
        CheckConstraint("coins_spent > 0", name="ck_redemption_coins"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"))
    reward_catalog_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reward_catalog.id", ondelete="RESTRICT")
    )
    status: Mapped[RewardStatus] = mapped_column(
        ENUM(RewardStatus, name="reward_status", create_type=True), default=RewardStatus.COMPLETED
    )
    coins_spent: Mapped[int] = mapped_column(Integer, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    redeemed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    metadata_jsonb: Mapped[dict] = mapped_column(JSONB, default=dict)
