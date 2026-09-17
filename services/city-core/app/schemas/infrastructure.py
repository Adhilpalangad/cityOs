from datetime import datetime

from pydantic import BaseModel, field_validator

from app.db.models import ASSET_CONDITIONS, RISK_LEVELS
from app.schemas.common import PageMeta


class InfrastructureAssetRead(BaseModel):
    id: str
    asset_code: str
    name: str
    asset_type: str
    department_code: str
    condition: str
    risk_level: str
    latitude: float | None = None
    longitude: float | None = None
    estimated_cost: float
    next_maintenance: datetime | None = None
    created_at: datetime
    updated_at: datetime


class InfrastructureAssetListResponse(BaseModel):
    items: list[InfrastructureAssetRead]
    meta: PageMeta


class InfrastructureAssetCreate(BaseModel):
    asset_code: str
    name: str
    asset_type: str
    department_code: str = "INFRASTRUCTURE"
    latitude: float | None = None
    longitude: float | None = None
    estimated_cost: float = 0.0
    next_maintenance: datetime | None = None


class InfrastructureAssetUpdate(BaseModel):
    name: str | None = None
    condition: str | None = None
    risk_level: str | None = None
    estimated_cost: float | None = None
    next_maintenance: datetime | None = None
    # Not persisted -- only annotates the audit entry written when
    # condition/risk_level actually changes.
    reason: str | None = None

    @field_validator("condition")
    @classmethod
    def _condition(cls, value: str | None) -> str | None:
        if value is not None and value not in ASSET_CONDITIONS:
            raise ValueError(f"condition must be one of {ASSET_CONDITIONS}")
        return value

    @field_validator("risk_level")
    @classmethod
    def _risk_level(cls, value: str | None) -> str | None:
        if value is not None and value not in RISK_LEVELS:
            raise ValueError(f"risk_level must be one of {RISK_LEVELS}")
        return value
