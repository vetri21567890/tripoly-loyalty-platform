from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings import LoyaltyProgramSetting


DEFAULT_PROGRAM_SETTINGS = {
    "coins_per_rupee": ("10", "int", "Travel Coins required for INR 1 redemption value."),
    "coin_expiry_months": ("24", "int", "Standard coin expiry duration in months."),
    "minimum_redemption_coins": ("500", "int", "Minimum Travel Coins required before redemption."),
    "partial_redemption_allowed": ("true", "bool", "Allow partial reward or booking redemptions when supported."),
    "max_redemption_per_booking": ("", "int", "Optional maximum Travel Coins redeemable per booking."),
}


class ProgramSettingsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def ensure_defaults(self) -> None:
        for key, (value, value_type, description) in DEFAULT_PROGRAM_SETTINGS.items():
            existing = await self.db.scalar(select(LoyaltyProgramSetting).where(LoyaltyProgramSetting.setting_key == key))
            if not existing:
                self.db.add(
                    LoyaltyProgramSetting(
                        setting_key=key,
                        setting_value=value,
                        value_type=value_type,
                        description=description,
                        is_active=True,
                    )
                )
        await self.db.flush()

    async def list_settings(self) -> list[LoyaltyProgramSetting]:
        await self.ensure_defaults()
        result = await self.db.execute(select(LoyaltyProgramSetting).order_by(LoyaltyProgramSetting.setting_key))
        return list(result.scalars().all())

    async def get(self, key: str, default=None):
        await self.ensure_defaults()
        setting = await self.db.scalar(
            select(LoyaltyProgramSetting).where(
                LoyaltyProgramSetting.setting_key == key,
                LoyaltyProgramSetting.is_active.is_(True),
            )
        )
        if not setting:
            return default
        return self.parse_value(setting.setting_value, setting.value_type, default)

    async def set(self, key: str, value, value_type: str | None = None, description: str | None = None) -> LoyaltyProgramSetting:
        await self.ensure_defaults()
        setting = await self.db.scalar(select(LoyaltyProgramSetting).where(LoyaltyProgramSetting.setting_key == key))
        resolved_type = value_type or self.infer_type(value)
        if not setting:
            setting = LoyaltyProgramSetting(setting_key=key, setting_value="", value_type=resolved_type, is_active=True)
            self.db.add(setting)
        setting.setting_value = self.serialize_value(value, resolved_type)
        setting.value_type = resolved_type
        if description is not None:
            setting.description = description
        setting.is_active = True
        await self.db.flush()
        return setting

    def serialize_value(self, value, value_type: str) -> str:
        if value is None:
            return ""
        if value_type == "bool":
            return "true" if bool(value) else "false"
        return str(value)

    def parse_value(self, value: str, value_type: str, default=None):
        if value == "":
            return default
        if value_type == "int":
            return int(value)
        if value_type == "float":
            return float(value)
        if value_type == "bool":
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return value

    def infer_type(self, value) -> str:
        if isinstance(value, bool):
            return "bool"
        if isinstance(value, int):
            return "int"
        if isinstance(value, float):
            return "float"
        return "string"

    async def coins_per_rupee(self) -> int:
        return int(await self.get("coins_per_rupee", 10))

    async def coins_to_rupees(self, coins: int) -> int:
        rate = await self.coins_per_rupee()
        if rate <= 0:
            rate = 10
        return coins // rate
