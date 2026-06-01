import enum


class CoinGrantStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    FULLY_REDEEMED = "fully_redeemed"


class ExpiryType(str, enum.Enum):
    STANDARD_24_MONTHS = "standard_24_months"
    CAMPAIGN_OVERRIDE = "campaign_override"
    NO_EXPIRY = "no_expiry"


class WalletOperationType(str, enum.Enum):
    EARN = "earn"
    REDEEM = "redeem"
    EXPIRE = "expire"
    ADJUST = "adjust"


class CoinTransactionDirection(str, enum.Enum):
    CREDIT = "credit"
    DEBIT = "debit"
    EXPIRE = "expire"


class RewardStatus(str, enum.Enum):
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class UgcType(str, enum.Enum):
    PHOTO = "photo"
    REVIEW_SCREENSHOT = "review_screenshot"
    TESTIMONIAL = "testimonial"
    VIDEO = "video"
    REEL = "reel"


class UgcAttemptStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class UgcModerationDecision(str, enum.Enum):
    APPROVE = "approve"
    REJECT = "reject"


class ReferralStatus(str, enum.Enum):
    INVITED = "invited"
    REGISTERED = "registered"
    PROFILE_COMPLETED = "profile_completed"
    BOOKING_CONFIRMED = "booking_confirmed"
    QUALIFIED = "qualified"
    REWARD_ISSUED = "reward_issued"


class LoyaltyTierCode(str, enum.Enum):
    EXPLORER = "EXPLORER"
    VOYAGER = "VOYAGER"
    ELITE_TRAVELLER = "ELITE_TRAVELLER"
    GLOBAL_NOMAD = "GLOBAL_NOMAD"


class CampaignType(str, enum.Enum):
    FESTIVAL = "festival"
    DESTINATION_LAUNCH = "destination_launch"
    INSIDER = "insider"


class CampaignEligibilityType(str, enum.Enum):
    ALL_CUSTOMERS = "ALL_CUSTOMERS"
    ENROLLED_ONLY = "ENROLLED_ONLY"
    INVITE_ONLY = "INVITE_ONLY"


class MissionStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class BookingValueSource(str, enum.Enum):
    PARTNER_BOOKING = "partner_booking"
    CRM_BOOKING = "crm_booking"
    MANUAL_TEST = "manual_test"
