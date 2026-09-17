from datetime import datetime

from pydantic import BaseModel, field_validator

from app.db.models import RISK_LEVELS, ROAD_STATUSES, TRAFFIC_LEVELS
from app.schemas.common import PageMeta

Waypoint = tuple[float, float]


class RoadRead(BaseModel):
    id: str
    code: str
    name: str
    road_type: str
    status: str
    capacity: int
    current_vehicle_count: int
    average_speed_kmh: float | None
    traffic_level: str
    risk_level: str
    waypoints: list[Waypoint]
    created_at: datetime
    updated_at: datetime


class RoadListResponse(BaseModel):
    items: list[RoadRead]
    meta: PageMeta


class RoadCreate(BaseModel):
    code: str
    name: str
    road_type: str = "local"
    capacity: int = 0
    waypoints: list[Waypoint] = []


class RoadUpdate(BaseModel):
    name: str | None = None
    status: str | None = None
    capacity: int | None = None
    current_vehicle_count: int | None = None
    average_speed_kmh: float | None = None
    traffic_level: str | None = None
    risk_level: str | None = None
    waypoints: list[Waypoint] | None = None

    @field_validator("status")
    @classmethod
    def _status(cls, value: str | None) -> str | None:
        if value is not None and value not in ROAD_STATUSES:
            raise ValueError(f"status must be one of {ROAD_STATUSES}")
        return value

    @field_validator("traffic_level")
    @classmethod
    def _traffic_level(cls, value: str | None) -> str | None:
        if value is not None and value not in TRAFFIC_LEVELS:
            raise ValueError(f"traffic_level must be one of {TRAFFIC_LEVELS}")
        return value

    @field_validator("risk_level")
    @classmethod
    def _risk_level(cls, value: str | None) -> str | None:
        if value is not None and value not in RISK_LEVELS:
            raise ValueError(f"risk_level must be one of {RISK_LEVELS}")
        return value
