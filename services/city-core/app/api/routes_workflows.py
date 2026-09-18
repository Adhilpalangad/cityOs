"""Government Workflow Engine (spec section 45).

Replaces the GET-only, self-seeded stub that used to live in
routes_extended.py: real create/assign/status-transition endpoints, backed
by app/services/workflows.py's enforced lifecycle and app/services/audit.py
for the sensitive transitions (spec's own example: approval/rejection are
exactly the kind of action section 50 wants logged).

No DELETE endpoint, matching incidents' reasoning (see routes_incidents.py):
a workflow task is part of the department's audit trail once created, not
something that should be able to disappear.
"""

import math
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db, require_permission
from app.core.errors import AppError
from app.db.models import WorkflowTask
from app.schemas.common import PageMeta
from app.schemas.workflows import (
    WorkflowTaskAssign,
    WorkflowTaskCreate,
    WorkflowTaskListResponse,
    WorkflowTaskRead,
    WorkflowTaskStatusUpdate,
    WorkflowTaskUpdate,
)
from app.services import audit
from app.services.workflows import generate_task_number, validate_transition

router = APIRouter(prefix="/api/v1/workflows", tags=["workflows"])


def _to_read(task: WorkflowTask) -> WorkflowTaskRead:
    return WorkflowTaskRead(
        id=str(task.id),
        task_number=task.task_number,
        title=task.title,
        department_code=task.department_code,
        assigned_to=task.assigned_to,
        priority=task.priority,
        status=task.status,
        sla_deadline=task.sla_deadline,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


async def _load_or_404(db: AsyncSession, task_id: uuid.UUID) -> WorkflowTask:
    task = await db.get(WorkflowTask, task_id)
    if task is None:
        raise AppError(
            404, "WORKFLOW_TASK_NOT_FOUND", "The requested workflow task does not exist."
        )
    return task


@router.get(
    "",
    response_model=WorkflowTaskListResponse,
    dependencies=[Depends(require_permission("workflow.read"))],
)
async def list_workflow_tasks(
    db: AsyncSession = Depends(get_db),
    q: str | None = Query(default=None, description="Search by task number or title"),
    status_filter: str | None = Query(default=None, alias="status"),
    department_code: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> WorkflowTaskListResponse:
    stmt = select(WorkflowTask)
    if q:
        pattern = f"%{q.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(WorkflowTask.task_number).like(pattern),
                func.lower(WorkflowTask.title).like(pattern),
            )
        )
    if status_filter:
        stmt = stmt.where(WorkflowTask.status == status_filter)
    if department_code:
        stmt = stmt.where(WorkflowTask.department_code == department_code)

    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    stmt = (
        stmt.order_by(WorkflowTask.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    tasks = (await db.scalars(stmt)).all()

    return WorkflowTaskListResponse(
        items=[_to_read(t) for t in tasks],
        meta=PageMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=max(1, math.ceil(total / page_size)),
        ),
    )


@router.get("/{task_id}", response_model=WorkflowTaskRead)
async def get_workflow_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_permission("workflow.read")),
) -> WorkflowTaskRead:
    return _to_read(await _load_or_404(db, task_id))


@router.post("", response_model=WorkflowTaskRead, status_code=201)
async def create_workflow_task(
    payload: WorkflowTaskCreate,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_permission("workflow.create")),
) -> WorkflowTaskRead:
    task = WorkflowTask(
        task_number=generate_task_number(),
        title=payload.title,
        department_code=payload.department_code,
        priority=payload.priority,
        sla_deadline=payload.sla_deadline,
        status="PENDING",
    )
    db.add(task)
    await db.commit()
    return _to_read(task)


@router.patch("/{task_id}", response_model=WorkflowTaskRead)
async def update_workflow_task(
    task_id: uuid.UUID,
    payload: WorkflowTaskUpdate,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_permission("workflow.update")),
) -> WorkflowTaskRead:
    task = await _load_or_404(db, task_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    await db.commit()
    return _to_read(task)


@router.post("/{task_id}/assign", response_model=WorkflowTaskRead)
async def assign_workflow_task(
    task_id: uuid.UUID,
    payload: WorkflowTaskAssign,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_permission("workflow.assign")),
) -> WorkflowTaskRead:
    task = await _load_or_404(db, task_id)
    task.assigned_to = payload.assigned_to
    audit.record(
        db,
        actor=user.email,
        action=f"WORKFLOW_TASK_ASSIGNED_TO_{payload.assigned_to}",
        target_resource=task.task_number,
        department_code=task.department_code,
        reason=payload.reason,
    )
    await db.commit()
    return _to_read(task)


@router.patch("/{task_id}/status", response_model=WorkflowTaskRead)
async def update_workflow_task_status(
    task_id: uuid.UUID,
    payload: WorkflowTaskStatusUpdate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_permission("workflow.update")),
) -> WorkflowTaskRead:
    task = await _load_or_404(db, task_id)
    validate_transition(task.status, payload.status)
    previous_status = task.status
    task.status = payload.status

    # Every transition out of PENDING/IN_PROGRESS via this endpoint is one
    # of approval (COMPLETED), rejection (REJECTED), or escalation
    # (ESCALATED) -- spec section 45's own list of sensitive actions.
    audit.record(
        db,
        actor=user.email,
        action=f"WORKFLOW_TASK_{previous_status}_TO_{payload.status}",
        target_resource=task.task_number,
        department_code=task.department_code,
        reason=payload.reason,
    )
    await db.commit()
    return _to_read(task)
