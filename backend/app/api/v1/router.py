from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    analytics,
    auth,
    campaigns,
    missions,
    notifications,
    profile,
    referrals,
    rewards,
    tiers,
    ugc,
    wallet,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(profile.router, prefix="/customers", tags=["Customer Profile"])
api_router.include_router(wallet.router, prefix="/wallet", tags=["Wallet"])
api_router.include_router(tiers.router, prefix="/tiers", tags=["Loyalty Tiers"])
api_router.include_router(referrals.router, prefix="/referrals", tags=["Referrals"])
api_router.include_router(rewards.router, prefix="/rewards", tags=["Rewards Marketplace"])
api_router.include_router(campaigns.router, prefix="/campaigns", tags=["Campaigns"])
api_router.include_router(missions.router, prefix="/missions", tags=["Missions"])
api_router.include_router(ugc.router, prefix="/ugc", tags=["UGC"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin Portal"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
