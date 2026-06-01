from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError
from app.models.booking import BookingEvent, CustomerFirstBooking
from app.services.earning_service import EarningService
from app.services.referral_service import ReferralService


class BookingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def confirm_booking(
        self,
        source_system: str,
        source_booking_id: str,
        customer_id: UUID,
        confirmed_at: datetime,
        booking_value_inr: Decimal,
        payload: dict | None = None,
    ) -> BookingEvent:
        existing = await self.db.execute(
            select(BookingEvent).where(
                BookingEvent.source_system == source_system,
                BookingEvent.source_booking_id == source_booking_id,
            )
        )
        event = existing.scalar_one_or_none()
        if event:
            return event

        event = BookingEvent(
            source_system=source_system,
            source_booking_id=source_booking_id,
            customer_id=customer_id,
            confirmed_at=confirmed_at,
            booking_value_inr=booking_value_inr,
            payload_jsonb=payload or {},
        )
        self.db.add(event)
        await self.db.flush()

        first_result = await self.db.execute(
            select(CustomerFirstBooking).where(CustomerFirstBooking.customer_id == customer_id)
        )
        is_first = first_result.scalar_one_or_none() is None
        if is_first:
            self.db.add(
                CustomerFirstBooking(
                    customer_id=customer_id,
                    booking_event_id=event.id,
                    confirmed_at=confirmed_at,
                )
            )

        earning = EarningService(self.db)
        coins = await earning.issue_booking_bonus(customer_id, event.id, booking_value_inr)
        event.coins_awarded = coins

        if is_first:
            referral = ReferralService(self.db)
            await referral.on_first_booking_confirmed(customer_id, event.id)

        await self.db.flush()
        return event
