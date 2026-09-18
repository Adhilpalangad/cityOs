from datetime import datetime

from pydantic import BaseModel, field_validator

from app.db.models import WORKFLOW_PRIORITIES, WORKFLOW_STATUSES
from app.schemas.common import PageMeta


class WorkflowTaskRead(BaseModel):
    id: str
    task_number: str
    title: str
    department_code: str
    assigned_to: str | None = None
    priority: str
    status: str
    sla_deadline: datetime | None = None
    created_at: datetime
    updated_at: datetime


class WorkflowTaskListResponse(BaseModel):
    items: list[WorkflowTaskRead]
    meta: PageMeta


class WorkflowTaskCreate(BaseModel):
    title: str
    department_code: str
    priority: str = "MEDIUM"
    sla_deadline: datetime | None = None

    @field_validator("priority")
    @classmethod
    def _priority(cls, value: str) -> str:
        if value not in WORKFLOW_PRIORITIES:
            raise ValueError(f"priority must be one of {WORKFLOW_PRIORITIES}")
        return value


class WorkflowTaskUpdate(BaseModel):
    title: str | None = None
    priority: str | None = None
    sla_deadline: datetime | None = None

    @field_validator("priority")
    @classmethod
    def _priority(cls, value: str | None) -> str | None:
        if value is not None and value not in WORKFLOW_PRIORITIES:
            raise ValueError(f"priority must be one of {WORKFLOW_PRIORITIES}")
        return value


class WorkflowTaskAssign(BaseModel):
    assigned_to: str
    reason: str | None = None


class WorkflowTaskStatusUpdate(BaseModel):
    status: str
    reason: str | None = None

    @field_validator("status")
    @classmethod
    def _status(cls, value: str) -> str:
        if value not in WORKFLOW_STATUSES:
            raise ValueError(f"status must be one of {WORKFLOW_STATUSES}")
        return value
