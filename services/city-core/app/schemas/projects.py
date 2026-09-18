from datetime import datetime

from pydantic import BaseModel, computed_field, field_validator

from app.db.models import PROJECT_STATUSES
from app.schemas.common import PageMeta


class CityProjectRead(BaseModel):
    id: str
    project_code: str
    name: str
    department_code: str
    budget: float
    spent: float
    status: str
    completion_percentage: float
    created_at: datetime
    updated_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def variance_pct(self) -> float:
        """Spend as a percentage of budget -- spec section 46's worked
        example shows this directly ("Variance: Within expected range")."""
        if self.budget <= 0:
            return 0.0
        return round((self.spent / self.budget) * 100, 1)


class CityProjectListResponse(BaseModel):
    items: list[CityProjectRead]
    meta: PageMeta


class CityProjectCreate(BaseModel):
    project_code: str
    name: str
    department_code: str
    budget: float = 0.0


class CityProjectUpdate(BaseModel):
    name: str | None = None
    status: str | None = None
    completion_percentage: float | None = None

    @field_validator("status")
    @classmethod
    def _status(cls, value: str | None) -> str | None:
        if value is not None and value not in PROJECT_STATUSES:
            raise ValueError(f"status must be one of {PROJECT_STATUSES}")
        return value

    @field_validator("completion_percentage")
    @classmethod
    def _completion(cls, value: float | None) -> float | None:
        if value is not None and not (0 <= value <= 100):
            raise ValueError("completion_percentage must be between 0 and 100")
        return value


class CityProjectSpend(BaseModel):
    amount: float
    reason: str | None = None

    @field_validator("amount")
    @classmethod
    def _positive(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("amount must be positive")
        return value
