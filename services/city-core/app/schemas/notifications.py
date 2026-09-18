from datetime import datetime

from pydantic import BaseModel, field_validator

from app.db.models import NOTIFICATION_CHANNELS, NOTIFICATION_SEVERITIES
from app.schemas.common import PageMeta


class NotificationRead(BaseModel):
    id: str
    title: str
    message: str
    severity: str
    target_department: str | None = None
    channel: str
    is_read: bool
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationRead]
    meta: PageMeta


class NotificationCreate(BaseModel):
    title: str
    message: str
    severity: str = "INFO"
    target_department: str | None = None
    channel: str = "IN_APP"

    @field_validator("severity")
    @classmethod
    def _severity(cls, value: str) -> str:
        if value not in NOTIFICATION_SEVERITIES:
            raise ValueError(f"severity must be one of {NOTIFICATION_SEVERITIES}")
        return value

    @field_validator("channel")
    @classmethod
    def _channel(cls, value: str) -> str:
        if value not in NOTIFICATION_CHANNELS:
            raise ValueError(f"channel must be one of {NOTIFICATION_CHANNELS}")
        return value
