from datetime import datetime

from pydantic import BaseModel, field_validator

from app.db.models import VEHICLE_STATUSES, VEHICLE_TYPES
from app.schemas.common import PageMeta


class VehicleRead(BaseModel):
    id: str
    vehicle_id: str
    vehicle_type: str
    status: str
    latitude: float | None
    longitude: float | None
    speed_kmh: float | None
    heading_degrees: float | None
    position_updated_at: datetime | None
    created_at: datetime
    updated_at: datetime


class VehicleListResponse(BaseModel):
    items: list[VehicleRead]
    meta: PageMeta


class VehicleCreate(BaseModel):
    vehicle_id: str
    vehicle_type: str

    @field_validator("vehicle_type")
    @classmethod
    def _type(cls, value: str) -> str:
        if value not in VEHICLE_TYPES:
            raise ValueError(f"vehicle_type must be one of {VEHICLE_TYPES}")
        return value


class VehicleUpdate(BaseModel):
    status: str | None = None

    @field_validator("status")
    @classmethod
    def _status(cls, value: str | None) -> str | None:
        if value is not None and value not in VEHICLE_STATUSES:
            raise ValueError(f"status must be one of {VEHICLE_STATUSES}")
        return value


class VehiclePositionUpdate(BaseModel):
    """Matches the software Vehicle Data Provider event shape (spec section 14)."""

    latitude: float
    longitude: float
    speed_kmh: float
    heading_degrees: float
