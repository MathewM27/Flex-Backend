"""Application configuration loaded from environment via pydantic-settings.

Required values missing at startup abort the process (NFR-O2).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["local", "staging", "prod"]
NotificationProvider = Literal["console", "twilio"]
PaymentProvider = Literal["mock"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: Environment = "local"
    app_name: str = "flex-backend"
    log_level: str = "INFO"

    # Database
    database_url: str = Field(..., description="Async SQLAlchemy DSN")

    # Auth
    jwt_secret: str = Field(..., min_length=32)
    jwt_expires_minutes: int = 1440

    # CORS — comma-separated string parsed below
    cors_origins: str = ""

    # Notifications
    notification_provider: NotificationProvider = "console"
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""

    # Payments
    payment_provider: PaymentProvider = "mock"
    payment_webhook_secret: str = Field(..., min_length=16)

    # Booking
    booking_payment_timeout_minutes: int = 15

    @field_validator("jwt_secret")
    @classmethod
    def _no_placeholder_jwt(cls, value: str) -> str:
        if "change-me" in value:
            raise ValueError("JWT_SECRET still set to placeholder value")
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "prod"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Returns a cached Settings instance. Tests override via dependency_overrides."""
    return Settings()
