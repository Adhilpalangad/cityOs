from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"), env_file_encoding="utf-8", extra="ignore"
    )

    app_env: Literal["development", "test", "staging", "production"] = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8002
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000"
    # Its own database, not api-gateway's `cityos` -- see
    # infrastructure/postgres/init-databases.sql for why each service
    # needs a separate database rather than just separate tables.
    database_url: str = "postgresql+asyncpg://cityos:cityos_dev_only@localhost:5432/cityos_city_core"
    redis_url: str = "redis://localhost:6379/0"
    # Consumed by app/services/live_ingest.py's background task, which turns
    # the traffic/vehicles data providers' events into live Road/Vehicle
    # updates. Same field name and default as api-gateway's Settings.
    kafka_brokers: str = "localhost:19092"

    # Must match the identity service's JWT_SECRET: city-core verifies
    # access tokens identity issued, it does not issue its own.
    jwt_secret: str = "dev-only-insecure-secret-change-me"
    jwt_algorithm: str = "HS256"

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def async_database_url(self) -> str:
        return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)


@lru_cache
def get_settings() -> Settings:
    return Settings()
