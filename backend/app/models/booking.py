import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import BookingValueSource
from app.models.mixins import SoftDeleteMixin, TimestampMixin


class BookingEvent(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "booking_events"
    __table_args__ = (UniqueConstraint("source_system", "source_booking_id", name="uq_booking_source"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_system: Mapped[str] = mapped_column(String(64), nullable=False)
    source_booking_id: Mapped[str] = mapped_column(String(128), nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"))
    confirmed_at: Mapped[datetime] = mapped_column()
    booking_value_inr: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    value_source: Mapped[BookingValueSource] = mapped_column(
        ENUM(BookingValueSource, name="booking_value_source", create_type=True),
        default=BookingValueSource.PARTNER_BOOKING,
    )
    payload_jsonb: Mapped[dict] = mapped_column(JSONB, default=dict)
    coins_awarded: Mapped[int | None] = mapped_column()


class CustomerFirstBooking(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "customer_first_bookings"

    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), primary_key=True
    )
    booking_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("booking_events.id", ondelete="RESTRICT")
    )
    confirmed_at: Mapped[datetime] = mapped_column()
