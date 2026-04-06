"""Application configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    app_name: str = "AirTicket Travel Planner"
    debug: bool = False

    # Database — defaults to SQLite for local dev
    database_url: str = "sqlite+aiosqlite:///./airticket.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Twilio (SMS)
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""

    # S3
    s3_bucket: str = "airticket-uploads"
    s3_region: str = "ap-northeast-1"

    # Ticket search
    ticket_cache_ttl_seconds: int = 1800  # 30 minutes

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Render.com provides postgresql:// but asyncpg needs postgresql+asyncpg://
        if self.database_url.startswith("postgresql://"):
            self.database_url = self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)


settings = Settings()
