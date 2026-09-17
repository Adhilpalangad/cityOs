from datetime import datetime

from pydantic import BaseModel, field_validator

from app.db.models import INCIDENT_SEVERITIES, INCIDENT_STATUSES, INCIDENT_TYPES
from app.schemas.common import PageMeta


class IncidentRead(BaseModel):
    id: str
    incident_number: str
    incident_type: str
    severity: str
    status: str
    description: str | None
    latitude: float | None
    longitude: float | None
    road_id: str | None
    reporter: str | None
    department_code: str | None
    assigned_to: str | None
    response_time_seconds: int | None
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime


class IncidentListResponse(BaseModel):
    items: list[IncidentRead]
    meta: PageMeta


class IncidentCreate(BaseModel):
    incident_type: str
    severity: str
    description: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    road_id: str | None = None
    reporter: str | None = None
    department_code: str | None = None

    @field_validator("incident_type")
    @classmethod
    def _type(cls, value: str) -> str:
        if value not in INCIDENT_TYPES:
            raise ValueError(f"incident_type must be one of {INCIDENT_TYPES}")
        return value

    @field_validator("severity")
    @classmethod
    def _severity(cls, value: str) -> str:
        if value not in INCIDENT_SEVERITIES:
            raise ValueError(f"severity must be one of {INCIDENT_SEVERITIES}")
        return value


class IncidentUpdate(BaseModel):
    severity: str | None = None
    description: str | None = None
    department_code: str | None = None

    @field_validator("severity")
    @classmethod
    def _severity(cls, value: str | None) -> str | None:
        if value is not None and value not in INCIDENT_SEVERITIES:
            raise ValueError(f"severity must be one of {INCIDENT_SEVERITIES}")
        return value


class IncidentStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def _status(cls, value: str) -> str:
        if value not in INCIDENT_STATUSES:
            raise ValueError(f"status must be one of {INCIDENT_STATUSES}")
        return value


class IncidentAssign(BaseModel):
    assigned_to: str
