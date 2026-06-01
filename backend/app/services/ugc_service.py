import hashlib
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ValidationError
from app.models.enums import UgcAttemptStatus, UgcModerationDecision, UgcType
from app.models.ugc import UgcAttempt, UgcModerationAction, UgcSubmissionLimit, UgcThread
from app.services.earning_service import EarningService


class UgcService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def content_hash(object_key: str, metadata: dict) -> str:
        payload = f"{object_key}:{sorted(metadata.items())}"
        return hashlib.sha256(payload.encode()).hexdigest()

    async def check_submission_limits(self, customer_id: UUID, ugc_type: UgcType) -> None:
        limit_result = await self.db.execute(
            select(UgcSubmissionLimit).where(UgcSubmissionLimit.ugc_type == ugc_type)
        )
        limits = limit_result.scalar_one_or_none()
        daily_limit = limits.daily_limit if limits else 5
        monthly_limit = limits.monthly_limit if limits else 20

        now = datetime.now(timezone.utc)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = day_start.replace(day=1)

        daily_count = await self.db.scalar(
            select(func.count(UgcAttempt.id))
            .join(UgcThread)
            .where(
                UgcThread.customer_id == customer_id,
                UgcThread.ugc_type == ugc_type,
                UgcAttempt.created_at >= day_start,
            )
        )
        if daily_count and daily_count >= daily_limit:
            raise ValidationError(f"Daily submission limit ({daily_limit}) reached for {ugc_type.value}")

        monthly_count = await self.db.scalar(
            select(func.count(UgcAttempt.id))
            .join(UgcThread)
            .where(
                UgcThread.customer_id == customer_id,
                UgcThread.ugc_type == ugc_type,
                UgcAttempt.created_at >= month_start,
            )
        )
        if monthly_count and monthly_count >= monthly_limit:
            raise ValidationError(f"Monthly submission limit ({monthly_limit}) reached for {ugc_type.value}")

    async def check_duplicate(self, customer_id: UUID, content_hash: str) -> None:
        dup = await self.db.execute(
            select(UgcAttempt)
            .join(UgcThread)
            .where(
                UgcThread.customer_id == customer_id,
                UgcAttempt.content_hash == content_hash,
                UgcAttempt.status.in_([UgcAttemptStatus.PENDING, UgcAttemptStatus.APPROVED]),
            )
        )
        if dup.scalar_one_or_none():
            raise ConflictError("Duplicate submission detected", code="UGC_DUPLICATE")

    async def init_upload(
        self, customer_id: UUID, ugc_type: UgcType, destination: str | None, thread_id: UUID | None
    ) -> dict:
        await self.check_submission_limits(customer_id, ugc_type)
        if thread_id:
            thread_result = await self.db.execute(
                select(UgcThread).where(UgcThread.id == thread_id, UgcThread.customer_id == customer_id)
            )
            thread = thread_result.scalar_one_or_none()
            if not thread:
                raise ValidationError("Invalid UGC thread")
        else:
            thread = UgcThread(customer_id=customer_id, ugc_type=ugc_type, destination=destination)
            self.db.add(thread)
            await self.db.flush()

        object_key = f"ugc/{customer_id}/{thread.id}/{uuid4()}"
        return {
            "ugc_thread_id": thread.id,
            "upload_url": f"https://storage.example.com/upload?key={object_key}",
            "object_key": object_key,
            "expires_in_seconds": 3600,
        }

    async def complete_upload(
        self,
        customer_id: UUID,
        thread_id: UUID,
        media_object_key: str,
        content_metadata: dict,
    ) -> UgcAttempt:
        thread_result = await self.db.execute(
            select(UgcThread).where(UgcThread.id == thread_id, UgcThread.customer_id == customer_id)
        )
        thread = thread_result.scalar_one_or_none()
        if not thread:
            raise ValidationError("Invalid UGC thread")

        content_hash = self.content_hash(media_object_key, content_metadata)
        await self.check_duplicate(customer_id, content_hash)

        attempt = UgcAttempt(
            ugc_thread_id=thread.id,
            status=UgcAttemptStatus.PENDING,
            media_object_key=media_object_key,
            content_hash=content_hash,
            content_metadata_jsonb=content_metadata,
        )
        self.db.add(attempt)
        await self.db.flush()
        return attempt

    async def moderate(
        self, ugc_attempt_id: UUID, admin_user_id: UUID, decision: UgcModerationDecision, rejection_reason: str | None
    ) -> UgcAttempt:
        result = await self.db.execute(select(UgcAttempt).where(UgcAttempt.id == ugc_attempt_id))
        attempt = result.scalar_one_or_none()
        if not attempt or attempt.status != UgcAttemptStatus.PENDING:
            raise ValidationError("UGC attempt not pending")

        existing_mod = await self.db.execute(
            select(UgcModerationAction).where(UgcModerationAction.ugc_attempt_id == ugc_attempt_id)
        )
        if existing_mod.scalar_one_or_none():
            raise ConflictError("Already moderated")

        self.db.add(
            UgcModerationAction(
                ugc_attempt_id=ugc_attempt_id,
                admin_user_id=admin_user_id,
                decision=decision,
                rejection_reason=rejection_reason,
                decided_at=datetime.now(timezone.utc),
            )
        )

        if decision == UgcModerationDecision.APPROVE:
            attempt.status = UgcAttemptStatus.APPROVED
            thread_result = await self.db.execute(select(UgcThread).where(UgcThread.id == attempt.ugc_thread_id))
            thread = thread_result.scalar_one()
            earning = EarningService(self.db)
            await earning.issue_ugc_reward(thread.customer_id, attempt.id, thread.ugc_type.value)
        else:
            attempt.status = UgcAttemptStatus.REJECTED
            attempt.rejection_reason = rejection_reason

        attempt.decided_at = datetime.now(timezone.utc)
        await self.db.flush()
        return attempt
