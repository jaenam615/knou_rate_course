"""
Application configuration loaded from environment variables.

All settings must be provided via environment variables or .env file.
No hardcoded defaults for URLs or secrets.
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str

    redis_url: str | None = None  # Optional - falls back to in-memory cache

    debug: bool = False

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    frontend_url: str

    sendgrid_api_key: str = ""  # Optional - emails won't send if not set
    from_email: str = ""

    sentry_dsn: str = ""  # Optional - error tracking disabled if not set

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """Warn if JWT secret is too short in production."""
        if len(v) < 32:
            import logging
            logging.warning(
                "JWT_SECRET_KEY is less than 32 characters. "
                "Use a stronger secret in production."
            )
        return v


settings = Settings()
