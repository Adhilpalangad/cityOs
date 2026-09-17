from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["healthy"] = "healthy"
    service: Literal["api-gateway"] = "api-gateway"


class ReadinessResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    dependencies: dict[str, Literal["healthy", "unhealthy"]]


class SystemInfo(BaseModel):
    name: Literal["CityOS"] = "CityOS"
    service: Literal["api-gateway"] = "api-gateway"
    version: str
    environment: str
