import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import ReferralStatus
from app.models.mixins import SoftDeleteMixin, TimestampMixin


class ReferralCode(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "referral_codes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"))
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="active")


class ReferralAttribution(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "referral_attributions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    referral_code_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("referral_codes.id", ondelete="CASCADE")
    )
    referrer_customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE")
    )
    referred_customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL")
    )
    referred_phone: Mapped[str | None] = mapped_column(String(20))
    referred_email: Mapped[str | None] = mapped_column(String(255))
    referral_link_hash: Mapped[str | None] = mapped_column(String(128))
    referral_source: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[ReferralStatus] = mapped_column(
        ENUM(ReferralStatus, name="referral_status", create_type=True), default=ReferralStatus.INVITED
    )
    invited_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    registered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    profile_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    booking_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    qualified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reward_issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ReferralStatusHistory(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "referral_status_history"
    __table_args__ = (UniqueConstraint("referral_attribution_id", "status", name="uq_referral_status_step"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    referral_attribution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("referral_attributions.id", ondelete="CASCADE")
    )
    status: Mapped[ReferralStatus] = mapped_column(ENUM(ReferralStatus, name="referral_status", create_type=True))
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    booking_event_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("booking_events.id"))
    coin_grant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("coin_grants.id"))
