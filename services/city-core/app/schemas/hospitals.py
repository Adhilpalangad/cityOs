from datetime import datetime

from pydantic import BaseModel, field_validator, model_validator

from app.db.models import CAPACITY_LEVELS, HOSPITAL_STATUSES
from app.schemas.common import PageMeta


class HospitalRead(BaseModel):
    id: str
    code: str
    name: str
    latitude: float
    longitude: float
    beds_total: int
    beds_occupied: int
    icu_total: int
    icu_occupied: int
    emergency_capacity: str
    status: str
    created_at: datetime
    updated_at: datetime


class HospitalListResponse(BaseModel):
    items: list[HospitalRead]
    meta: PageMeta


class HospitalCreate(BaseModel):
    code: str
    name: str
    latitude: float
    longitude: float
    beds_total: int = 0
    icu_total: int = 0

    @model_validator(mode="after")
    def _bounds(self) -> "HospitalCreate":
        if self.beds_total < 0 or self.icu_total < 0:
            raise ValueError("beds_total and icu_total cannot be negative.")
        return self


class HospitalUpdate(BaseModel):
    name: str | None = None
    beds_total: int | None = None
    beds_occupied: int | None = None
    icu_total: int | None = None
    icu_occupied: int | None = None
    emergency_capacity: str | None = None
    status: str | None = None

    @field_validator("status")
    @classmethod
    def _status(cls, value: str | None) -> str | None:
        if value is not None and value not in HOSPITAL_STATUSES:
            raise ValueError(f"status must be one of {HOSPITAL_STATUSES}")
        return value

    @field_validator("emergency_capacity")
    @classmethod
    def _capacity(cls, value: str | None) -> str | None:
        if value is not None and value not in CAPACITY_LEVELS:
            raise ValueError(f"emergency_capacity must be one of {CAPACITY_LEVELS}")
        return value
