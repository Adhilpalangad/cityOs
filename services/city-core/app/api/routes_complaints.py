"""Citizen Portal complaints (spec section 44).

Replaces the GET/POST-only stub that used to live in routes_extended.py.
Adds the rest of spec section 44's flow the old version never modeled:
Department Assignment -> Officer -> Resolution -> Citizen Notification,
enforced by app/services/complaints.py's transition map and wired to
app/services/audit.py (assignment/rejection/resolution are sensitive
actions) and app/services/notifications.py (resolution notifies the
citizen -- the closest this data model gets to spec's "Citizen
Notification" step, since there's no per-citizen account/session to target
here, only the reporter_email captured at submission).

No DELETE: a citizen's complaint history is a record, not something an
officer should be able to erase.
"""

import math
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db, require_permission
from app.core.errors import AppError
from app.db.models import CitizenComplaint
from app.schemas.common import PageMeta
from app.schemas.complaints import (
    CitizenComplaintCreate,
    CitizenComplaintListResponse,
    CitizenComplaintRead,
    CitizenComplaintStatusUpdate,
)
from app.services import audit
from app.services.complaints import generate_complaint_number, validate_transition
from app.services.notifications import notify

router = APIRouter(prefix="/api/v1/complaints", tags=["complaints"])


def _to_read(complaint: CitizenComplaint) -> CitizenComplaintRead:
    return CitizenComplaintRead(
        id=str(complaint.id),
        complaint_number=complaint.complaint_number,
        title=complaint.title,
        description=complaint.description,
        category=complaint.category,
        latitude=complaint.latitude,
        longitude=complaint.longitude,
        image_url=complaint.image_url,
        status=complaint.status,
        reporter_email=complaint.reporter_email,
        department_code=complaint.department_code,
        created_at=complaint.created_at,
        updated_at=complaint.updated_at,
    )


async def _load_or_404(db: AsyncSession, complaint_id: uuid.UUID) -> CitizenComplaint:
    complaint = await db.get(CitizenComplaint, complaint_id)
    if complaint is None:
        raise AppError(404, "COMPLAINT_NOT_FOUND", "The requested complaint does not exist.")
    return complaint


@router.get(
    "",
    response_model=CitizenComplaintListResponse,
    dependencies=[Depends(require_permission("complaint.read"))],
)
async def list_complaints(
    db: AsyncSession = Depends(get_db),
    q: str | None = Query(default=None, description="Search by complaint number or title"),
    status_filter: str | None = Query(default=None, alias="status"),
    department_code: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> CitizenComplaintListResponse:
    stmt = select(CitizenComplaint)
    if q:
        pattern = f"%{q.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(CitizenComplaint.complaint_number).like(pattern),
                func.lower(CitizenComplaint.title).like(pattern),
            )
        )
    if status_filter:
        stmt = stmt.where(CitizenComplaint.status == status_filter)
    if department_code:
        stmt = stmt.where(CitizenComplaint.department_code == department_code)

    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    stmt = (
        stmt.order_by(CitizenComplaint.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    complaints = (await db.scalars(stmt)).all()

    return CitizenComplaintListResponse(
        items=[_to_read(c) for c in complaints],
        meta=PageMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=max(1, math.ceil(total / page_size)),
        ),
    )


@router.get("/{complaint_id}", response_model=CitizenComplaintRead)
async def get_complaint(
    complaint_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_permission("complaint.read")),
) -> CitizenComplaintRead:
    return _to_read(await _load_or_404(db, complaint_id))


@router.post("", response_model=CitizenComplaintRead, status_code=201)
async def create_complaint(
    payload: CitizenComplaintCreate,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_permission("complaint.create")),
) -> CitizenComplaintRead:
    complaint = CitizenComplaint(
        complaint_number=generate_complaint_number(),
        title=payload.title,
        description=payload.description,
        category=payload.category,
        latitude=payload.latitude,
        longitude=payload.longitude,
        image_url=payload.image_url,
        reporter_email=payload.reporter_email,
        status="SUBMITTED",
    )
    db.add(complaint)
    await db.commit()
    return _to_read(complaint)


@router.patch("/{complaint_id}/status", response_model=CitizenComplaintRead)
async def update_complaint_status(
    complaint_id: uuid.UUID,
    payload: CitizenComplaintStatusUpdate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_permission("complaint.update")),
) -> CitizenComplaintRead:
    complaint = await _load_or_404(db, complaint_id)
    validate_transition(complaint.status, payload.status)
    previous_status = complaint.status
    complaint.status = payload.status
    if payload.status == "ASSIGNED" and payload.department_code:
        complaint.department_code = payload.department_code

    audit.record(
        db,
        actor=user.email,
        action=f"COMPLAINT_{previous_status}_TO_{payload.status}",
        target_resource=complaint.complaint_number,
        department_code=complaint.department_code or user.department,
        reason=payload.reason,
    )

    # Spec section 44's flow ends with "Citizen Notification" on
    # resolution. No per-citizen session to target -- the reporter's email
    # captured at submission is the closest this data model gets.
    if payload.status == "RESOLVED" and complaint.reporter_email:
        notify(
            db,
            title=f"Your complaint {complaint.complaint_number} has been resolved",
            message=payload.reason or f"'{complaint.title}' has been marked resolved.",
            severity="INFO",
            channel="EMAIL",
        )

    await db.commit()
    return _to_read(complaint)
