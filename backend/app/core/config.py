from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Tripoly Loyalty Platform"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    integrations_prefix: str = "/api/integrations"

    database_url: str = "postgresql+asyncpg://tripoly:tripoly_secret@localhost:5432/tripoly_loyalty"
    database_url_sync: str = "postgresql://tripoly:tripoly_secret@localhost:5432/tripoly_loyalty"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    otp_expire_minutes: int = 10
    otp_max_attempts: int = 5
    otp_lockout_minutes: int = 30

    cors_origins: str = "http://localhost:5173,http://localhost:5174"
    cors_origin_regex: str | None = (
        r"https?://("
        r"localhost|127\.0\.0\.1|0\.0\.0\.0|"
        r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
        r"172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}|"
        r"192\.168\.\d{1,3}\.\d{1,3}|"
        r".*\.ngrok-free\.app|.*\.ngrok\.io"
        r")(:\d+)?"
    )
    partner_api_key: str = "dev-partner-key-change-in-production"

    coin_standard_expiry_months: int = 24

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
