import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin


class Customer(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)

    profile: Mapped["CustomerProfile | None"] = relationship(back_populates="customer", uselist=False)
    wallet_balance: Mapped["WalletBalance | None"] = relationship(
        "WalletBalance", back_populates="customer", uselist=False
    )


class CustomerProfile(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "customer_profiles"

    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), primary_key=True
    )
    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))
    birthday: Mapped[date | None] = mapped_column(Date)
    avatar_object_key: Mapped[str | None] = mapped_column(String(512))
    profile_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    customer: Mapped["Customer"] = relationship(back_populates="profile")


class CustomerTravelPreferences(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "customer_travel_preferences"

    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), primary_key=True
    )
    preferences_jsonb: Mapped[dict] = mapped_column(JSONB, default=dict)


class CustomerDevice(Base, TimestampMixin):
    """Anti-fraud: track devices for referral abuse prevention."""

    __tablename__ = "customer_devices"
    __table_args__ = (UniqueConstraint("customer_id", "device_fingerprint", name="uq_customer_device"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"))
    device_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
