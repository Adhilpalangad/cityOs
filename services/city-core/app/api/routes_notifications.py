"""Notification Engine (spec section 48).

Replaces routes_extended.py's GET-only, self-seeded Notification stub with
a real read/create/mark-read API. The actual "engine" part -- the trigger
rules that create notifications automatically -- lives in
app/services/notifications.py, called from routes_incidents.py,
routes_roads.py, and routes_hospitals.py rather than here; this file is
just the CRUD surface over the resulting rows.

No DELETE: a department's notification history is itself a record.
"""

import math
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db, require_permission
from app.core.errors import AppError
from app.db.models import Notification
from app.schemas.common import PageMeta
from app.schemas.notifications import (
    NotificationCreate,
    NotificationListResponse,
    NotificationRead,
)
from app.services.notifications import notify

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


def _to_read(n: Notification) -> NotificationRead:
    return NotificationRead(
        id=str(n.id),
        title=n.title,
        message=n.message,
        severity=n.severity,
        target_department=n.target_department,
        channel=n.channel,
        is_read=n.is_read,
        created_at=n.created_at,
    )


async def _load_or_404(db: AsyncSession, notification_id: uuid.UUID) -> Notification:
    notification = await db.get(Notification, notification_id)
    if notification is None:
        raise AppError(404, "NOTIFICATION_NOT_FOUND", "The requested notification does not exist.")
    return notification


@router.get(
    "",
    response_model=NotificationListResponse,
    dependencies=[Depends(require_permission("notification.read"))],
)
async def list_notifications(
    db: AsyncSession = Depends(get_db),
    is_read: bool | None = Query(default=None),
    severity: str | None = Query(default=None),
    target_department: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> NotificationListResponse:
    stmt = select(Notification)
    if is_read is not None:
        stmt = stmt.where(Notification.is_read == is_read)
    if severity:
        stmt = stmt.where(Notification.severity == severity)
    if target_department:
        stmt = stmt.where(Notification.target_department == target_department)

    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    stmt = (
        stmt.order_by(Notification.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    notifications = (await db.scalars(stmt)).all()

    return NotificationListResponse(
        items=[_to_read(n) for n in notifications],
        meta=PageMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=max(1, math.ceil(total / page_size)),
        ),
    )


@router.post("", response_model=NotificationRead, status_code=201)
async def create_notification(
    payload: NotificationCreate,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_permission("notification.create")),
) -> NotificationRead:
    entry = notify(
        db,
        title=payload.title,
        message=payload.message,
        severity=payload.severity,
        target_department=payload.target_department,
        channel=payload.channel,
    )
    await db.commit()
    return _to_read(entry)


@router.patch("/{notification_id}/read", response_model=NotificationRead)
async def mark_notification_read(
    notification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_permission("notification.read")),
) -> NotificationRead:
    notification = await _load_or_404(db, notification_id)
    notification.is_read = True
    await db.commit()
    return _to_read(notification)
