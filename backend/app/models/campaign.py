import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import CampaignEligibilityType, CampaignType, ExpiryType
from app.models.mixins import SoftDeleteMixin, TimestampMixin


class Campaign(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    type: Mapped[CampaignType] = mapped_column(ENUM(CampaignType, name="campaign_type", create_type=True))
    eligibility_type: Mapped[CampaignEligibilityType] = mapped_column(
        ENUM(CampaignEligibilityType, name="campaign_eligibility_type", create_type=True),
        default=CampaignEligibilityType.ALL_CUSTOMERS,
    )
    status: Mapped[str] = mapped_column(String(32), default="active")
    reward_coins: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tasks: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CampaignParticipation(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "campaign_participations"
    __table_args__ = (
        UniqueConstraint("customer_id", "campaign_id", name="uq_campaign_participation"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"))
    campaign_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(32), default="enrolled")
    enrolled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CampaignInvitation(Base, TimestampMixin, SoftDeleteMixin):
    """INVITE_ONLY campaigns."""

    __tablename__ = "campaign_invitations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"))
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"))
    invited_by_admin_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("admin_users.id"))
    status: Mapped[str] = mapped_column(String(32), default="invited")


class CampaignCoinExpiryPolicy(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "campaign_coin_expiry_policies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"))
    expiry_type: Mapped[ExpiryType] = mapped_column(ENUM(ExpiryType, name="expiry_type", create_type=True))
    campaign_expiry_months_override: Mapped[int | None] = mapped_column(Integer)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CampaignRewardRule(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "campaign_reward_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"))
    trigger_event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    coins_awarded: Mapped[int] = mapped_column(Integer, nullable=False)
    expiry_override_type: Mapped[ExpiryType | None] = mapped_column(ENUM(ExpiryType, name="expiry_type", create_type=True))
    expiry_override_months_override: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32), default="active")
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
