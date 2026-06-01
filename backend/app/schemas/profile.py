from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProfileResponse(BaseModel):
    customer_id: UUID
    first_name: str | None
    last_name: str | None
    birthday: date | None
    avatar_object_key: str | None
    profile_completed_at: datetime | None
    travel_preferences: dict = Field(default_factory=dict)


class ProfileUpdateRequest(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    birthday: date | None = None


class TravelPreferencesUpdateRequest(BaseModel):
    preferences: dict = Field(default_factory=dict)


class CompleteProfileResponse(BaseModel):
    profile_completed: bool
    coins_awarded: int
    wallet_balance: "WalletBalanceBrief"


class WalletBalanceBrief(BaseModel):
    available_coins: int
    lifetime_coins_earned: int
