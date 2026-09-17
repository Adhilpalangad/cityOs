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
    api_port: int = 8000
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000"
    database_url: str = "postgresql+asyncpg://cityos:cityos_dev_only@localhost:5432/cityos"
    redis_url: str = "redis://localhost:6379/0"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "cityos_dev_only"
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    kafka_brokers: str = "localhost:19092"
    object_storage_endpoint: str = "http://localhost:9000"
    object_storage_access_key: str = "cityos"
    object_storage_secret_key: str = Field(default="cityos_dev_only", repr=False)
    object_storage_bucket: str = "cityos-development"
    identity_service_url: str = "http://localhost:8001"
    city_core_service_url: str = "http://localhost:8002"

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def async_database_url(self) -> str:
        return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)


@lru_cache
def get_settings() -> Settings:
    return Settings()
