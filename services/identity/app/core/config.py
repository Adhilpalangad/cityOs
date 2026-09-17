from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"), env_file_encoding="utf-8", extra="ignore"
    )

    app_env: Literal["development", "test", "staging", "production"] = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8001
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000"
    # Its own database, not api-gateway's `cityos` -- see
    # infrastructure/postgres/init-databases.sql for why each service
    # needs a separate database rather than just separate tables.
    database_url: str = "postgresql+asyncpg://cityos:cityos_dev_only@localhost:5432/cityos_identity"
    redis_url: str = "redis://localhost:6379/0"
    frontend_url: str = "http://localhost:3000"

    # Tokens
    jwt_secret: str = Field(default="dev-only-insecure-secret-change-me", repr=False)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    email_verification_token_expire_hours: int = 24
    password_reset_token_expire_minutes: int = 30

    # Rate limiting
    login_rate_limit_attempts: int = 5
    login_rate_limit_window_seconds: int = 60

    # OAuth
    google_client_id: str | None = None
    google_client_secret: str | None = Field(default=None, repr=False)
    github_client_id: str | None = None
    github_client_secret: str | None = Field(default=None, repr=False)
    oauth_redirect_base_url: str = "http://localhost:8001"

    # Bootstrap (local/dev super administrator; skipped if unset)
    superadmin_email: str | None = None
    superadmin_password: str | None = Field(default=None, repr=False)

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def async_database_url(self) -> str:
        return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)


@lru_cache
def get_settings() -> Settings:
    return Settings()
