from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class WalletBalanceResponse(BaseModel):
    available_coins: int
    expired_coins: int
    lifetime_coins_earned: int
    redeemed_coins_to_date: int
    approx_redemption_value_inr: int
    coins_per_rupee: int
    conversion_rule: str


class CoinGrantResponse(BaseModel):
    coin_grant_id: UUID
    earned_date: date
    expiry_date: date | None
    amount_remaining: int
    amount_total: int
    status: str
    grant_source: str


class CoinTransactionResponse(BaseModel):
    transaction_id: UUID
    direction: str
    amount: int
    earned_date: date
    expiry_date: date | None
    reason_code: str
    created_at: datetime


class ExpiringSoonResponse(BaseModel):
    days: int
    total_amount_remaining: int
    grants: list[CoinGrantResponse]
