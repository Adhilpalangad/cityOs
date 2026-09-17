from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator

from app.db.models import USER_STATUSES
from app.schemas.common import PageMeta, validate_password_strength


class UserRead(BaseModel):
    id: str
    email: str
    full_name: str
    role_code: str
    department_code: str | None
    status: str
    email_verified: bool
    created_at: datetime
    last_login_at: datetime | None


class UserListResponse(BaseModel):
    items: list[UserRead]
    meta: PageMeta


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role_code: str
    department_code: str | None = None

    _validate_password = field_validator("password")(validate_password_strength)


class UserUpdate(BaseModel):
    full_name: str | None = None
    role_code: str | None = None
    department_code: str | None = None
    status: str | None = None

    @field_validator("status")
    @classmethod
    def _validate_status(cls, value: str | None) -> str | None:
        if value is not None and value not in USER_STATUSES:
            raise ValueError(f"status must be one of {USER_STATUSES}")
        return value
