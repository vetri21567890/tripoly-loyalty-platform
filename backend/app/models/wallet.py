import uuid
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import (
    CoinGrantStatus,
    CoinTransactionDirection,
    ExpiryType,
    WalletOperationType,
)
from app.models.mixins import TimestampMixin


class WalletOperation(Base, TimestampMixin):
    __tablename__ = "wallet_operations"
    __table_args__ = (UniqueConstraint("customer_id", "idempotency_key", name="uq_wallet_op_idempotency"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"))
    operation_type: Mapped[WalletOperationType] = mapped_column(
        ENUM(WalletOperationType, name="wallet_operation_type", create_type=True), nullable=False
    )
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    reference_type: Mapped[str | None] = mapped_column(String(64))
    reference_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    transactions: Mapped[list["CoinTransaction"]] = relationship(back_populates="wallet_operation")


class CoinGrant(Base, TimestampMixin):
    __tablename__ = "coin_grants"
    __table_args__ = (
        CheckConstraint("amount_total > 0", name="ck_coin_grant_amount_total"),
        CheckConstraint("amount_remaining >= 0", name="ck_coin_grant_amount_remaining"),
        Index(
            "ix_coin_grants_fifo",
            "customer_id",
            text("(expiry_date IS NULL)"),
            "expiry_date",
            "earned_date",
            "created_at",
            postgresql_where=text("status = 'ACTIVE'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"))
    grant_source: Mapped[str] = mapped_column(String(64), nullable=False)
    reference_type: Mapped[str | None] = mapped_column(String(64))
    reference_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    amount_total: Mapped[int] = mapped_column(Integer, nullable=False)
    amount_remaining: Mapped[int] = mapped_column(Integer, nullable=False)

    earned_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiry_type: Mapped[ExpiryType] = mapped_column(
        ENUM(ExpiryType, name="expiry_type", create_type=True), nullable=False
    )
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    status: Mapped[CoinGrantStatus] = mapped_column(
        ENUM(CoinGrantStatus, name="coin_grant_status", create_type=True), default=CoinGrantStatus.ACTIVE
    )
    expired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    amount_expired: Mapped[int] = mapped_column(Integer, default=0)

    campaign_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("campaigns.id"))
    ugc_attempt_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("ugc_attempts.id"))
    booking_event_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("booking_events.id"))
    referral_attribution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("referral_attributions.id")
    )
    reward_redemption_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reward_redemptions.id")
    )


class CoinTransaction(Base, TimestampMixin):
    """Immutable ledger - no soft delete."""

    __tablename__ = "coin_transactions"
    __table_args__ = (CheckConstraint("amount > 0", name="ck_coin_tx_amount"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wallet_operation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("wallet_operations.id", ondelete="CASCADE")
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"))
    coin_grant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("coin_grants.id", ondelete="CASCADE"))

    direction: Mapped[CoinTransactionDirection] = mapped_column(
        ENUM(CoinTransactionDirection, name="coin_transaction_direction", create_type=True), nullable=False
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)

    earned_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    reason_code: Mapped[str] = mapped_column(String(64), nullable=False)
    reference_type: Mapped[str | None] = mapped_column(String(64))
    reference_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    reward_redemption_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reward_redemptions.id")
    )

    wallet_operation: Mapped["WalletOperation"] = relationship(back_populates="transactions")


class WalletBalance(Base, TimestampMixin):
    __tablename__ = "wallet_balance"

    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), primary_key=True
    )
    available_coins: Mapped[int] = mapped_column(Integer, default=0)
    expired_coins: Mapped[int] = mapped_column(Integer, default=0)
    redeemed_coins_to_date: Mapped[int] = mapped_column(Integer, default=0)
    lifetime_coins_earned: Mapped[int] = mapped_column(Integer, default=0)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="wallet_balance")

