import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import MissionStatus
from app.models.mixins import SoftDeleteMixin, TimestampMixin


class Mission(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "missions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    is_one_time: Mapped[bool] = mapped_column(default=True)
    status: Mapped[str] = mapped_column(String(32), default="active")


class MissionRewardRule(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "mission_reward_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mission_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("missions.id", ondelete="CASCADE"))
    coins_awarded: Mapped[int] = mapped_column(Integer, nullable=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), default="active")


class CustomerMissionCompletion(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "customer_mission_completions"
    __table_args__ = (UniqueConstraint("customer_id", "mission_id", name="uq_customer_mission"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"))
    mission_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("missions.id", ondelete="CASCADE"))
    status: Mapped[MissionStatus] = mapped_column(
        ENUM(MissionStatus, name="mission_status", create_type=True), default=MissionStatus.AVAILABLE
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    coins_awarded: Mapped[int | None] = mapped_column(Integer)
    admin_notes: Mapped[str | None] = mapped_column(Text)
    coin_grant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("coin_grants.id"))
