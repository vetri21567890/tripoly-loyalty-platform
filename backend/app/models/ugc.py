import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import UgcAttemptStatus, UgcModerationDecision, UgcType
from app.models.mixins import SoftDeleteMixin, TimestampMixin


class UgcSubmissionLimit(Base, TimestampMixin, SoftDeleteMixin):
    """Admin-configurable daily/monthly limits per UGC type."""

    __tablename__ = "ugc_submission_limits"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ugc_type: Mapped[UgcType] = mapped_column(ENUM(UgcType, name="ugc_type", create_type=True), unique=True)
    daily_limit: Mapped[int] = mapped_column(Integer, default=5)
    monthly_limit: Mapped[int] = mapped_column(Integer, default=20)
    status: Mapped[str] = mapped_column(String(32), default="active")


class UgcRewardRule(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "ugc_reward_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ugc_type: Mapped[UgcType] = mapped_column(ENUM(UgcType, name="ugc_type", create_type=True), unique=True)
    coins_awarded: Mapped[int] = mapped_column(Integer, nullable=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), default="active")


class UgcThread(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "ugc_threads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"))
    ugc_type: Mapped[UgcType] = mapped_column(ENUM(UgcType, name="ugc_type", create_type=True))
    destination: Mapped[str | None] = mapped_column(String(255))


class UgcAttempt(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "ugc_attempts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ugc_thread_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ugc_threads.id", ondelete="CASCADE")
    )
    status: Mapped[UgcAttemptStatus] = mapped_column(
        ENUM(UgcAttemptStatus, name="ugc_attempt_status", create_type=True), default=UgcAttemptStatus.PENDING
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    media_object_key: Mapped[str] = mapped_column(String(512), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    content_metadata_jsonb: Mapped[dict] = mapped_column(JSONB, default=dict)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class UgcModerationAction(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "ugc_moderation_actions"
    __table_args__ = (UniqueConstraint("ugc_attempt_id", name="uq_ugc_moderation_attempt"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ugc_attempt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ugc_attempts.id", ondelete="CASCADE")
    )
    admin_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("admin_users.id", ondelete="RESTRICT")
    )
    decision: Mapped[UgcModerationDecision] = mapped_column(
        ENUM(UgcModerationDecision, name="ugc_moderation_decision", create_type=True)
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
