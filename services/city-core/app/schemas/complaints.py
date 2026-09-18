from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.db.models import COMPLAINT_STATUSES
from app.schemas.common import PageMeta


class CitizenComplaintRead(BaseModel):
    id: str
    complaint_number: str
    title: str
    description: str
    category: str
    latitude: float | None = None
    longitude: float | None = None
    image_url: str | None = None
    status: str
    reporter_email: str | None = None
    department_code: str | None = None
    created_at: datetime
    updated_at: datetime


class CitizenComplaintListResponse(BaseModel):
    items: list[CitizenComplaintRead]
    meta: PageMeta


class CitizenComplaintCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=150)
    description: str = Field(..., min_length=5)
    category: str = Field(default="General")
    latitude: float | None = None
    longitude: float | None = None
    image_url: str | None = None
    reporter_email: str | None = None


class CitizenComplaintStatusUpdate(BaseModel):
    status: str
    # Only meaningful (and required by the route) when moving to ASSIGNED --
    # spec section 44's "Department Assignment" step.
    department_code: str | None = None
    reason: str | None = None

    @field_validator("status")
    @classmethod
    def _status(cls, value: str) -> str:
        if value not in COMPLAINT_STATUSES:
            raise ValueError(f"status must be one of {COMPLAINT_STATUSES}")
        return value
