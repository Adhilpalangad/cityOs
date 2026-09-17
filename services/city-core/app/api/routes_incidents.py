import math
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db, require_permission
from app.core.errors import AppError
from app.db.models import Incident
from app.schemas.common import PageMeta
from app.schemas.incidents import (
    IncidentAssign,
    IncidentCreate,
    IncidentListResponse,
    IncidentRead,
    IncidentStatusUpdate,
    IncidentUpdate,
)
from app.services import audit
from app.services.incidents import generate_incident_number, require_status, validate_transition

router = APIRouter(prefix="/api/v1/incidents", tags=["incidents"])


def _to_read(incident: Incident) -> IncidentRead:
    return IncidentRead(
        id=str(incident.id),
        incident_number=incident.incident_number,
        incident_type=incident.incident_type,
        severity=incident.severity,
        status=incident.status,
        description=incident.description,
        latitude=incident.latitude,
        longitude=incident.longitude,
        road_id=str(incident.road_id) if incident.road_id else None,
        reporter=incident.reporter,
        department_code=incident.department_code,
        assigned_to=incident.assigned_to,
        response_time_seconds=incident.response_time_seconds,
        resolved_at=incident.resolved_at,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
    )


async def _load_or_404(db: AsyncSession, incident_id: uuid.UUID) -> Incident:
    incident = await db.get(Incident, incident_id)
    if incident is None:
        raise AppError(404, "INCIDENT_NOT_FOUND", "The requested incident does not exist.")
    return incident


@router.get(
    "",
    response_model=IncidentListResponse,
    dependencies=[Depends(require_permission("incident.read"))],
)
async def list_incidents(
    db: AsyncSession = Depends(get_db),
    q: str | None = Query(default=None, description="Search by incident number or description"),
    incident_type: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    department_code: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> IncidentListResponse:
    stmt = select(Incident)
    if q:
        pattern = f"%{q.lower()}%"
        stmt = stmt.where(
            func.lower(Incident.incident_number).like(pattern)
            | func.lower(func.coalesce(Incident.description, "")).like(pattern)
        )
    if incident_type:
        stmt = stmt.where(Incident.incident_type == incident_type)
    if severity:
        stmt = stmt.where(Incident.severity == severity)
    if status_filter:
        stmt = stmt.where(Incident.status == status_filter)
    if department_code:
        stmt = stmt.where(Incident.department_code == department_code)

    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    stmt = stmt.order_by(Incident.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    incidents = (await db.scalars(stmt)).all()

    return IncidentListResponse(
        items=[_to_read(incident) for incident in incidents],
        meta=PageMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=max(1, math.ceil(total / page_size)),
        ),
    )


@router.get(
    "/{incident_id}",
    response_model=IncidentRead,
    dependencies=[Depends(require_permission("incident.read"))],
)
async def get_incident(incident_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> IncidentRead:
    return _to_read(await _load_or_404(db, incident_id))


@router.post(
    "",
    response_model=IncidentRead,
    status_code=201,
    dependencies=[Depends(require_permission("incident.create"))],
)
async def create_incident(
    payload: IncidentCreate, db: AsyncSession = Depends(get_db)
) -> IncidentRead:
    road_uuid: uuid.UUID | None = None
    if payload.road_id is not None:
        try:
            road_uuid = uuid.UUID(payload.road_id)
        except ValueError as exc:
            raise AppError(400, "INVALID_ROAD_ID", "road_id must be a valid UUID.") from exc

    incident = Incident(
        incident_number=generate_incident_number(),
        incident_type=payload.incident_type,
        severity=payload.severity,
        description=payload.description,
        latitude=payload.latitude,
        longitude=payload.longitude,
        road_id=road_uuid,
        reporter=payload.reporter,
        department_code=payload.department_code,
        status="DETECTED",
    )
    db.add(incident)
    await db.commit()
    return _to_read(incident)


@router.patch(
    "/{incident_id}",
    response_model=IncidentRead,
    dependencies=[Depends(require_permission("incident.update"))],
)
async def update_incident(
    incident_id: uuid.UUID, payload: IncidentUpdate, db: AsyncSession = Depends(get_db)
) -> IncidentRead:
    incident = await _load_or_404(db, incident_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(incident, field, value)
    await db.commit()
    return _to_read(incident)


@router.patch("/{incident_id}/status", response_model=IncidentRead)
async def update_incident_status(
    incident_id: uuid.UUID,
    payload: IncidentStatusUpdate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_permission("incident.update")),
) -> IncidentRead:
    incident = await _load_or_404(db, incident_id)
    validate_transition(incident.status, payload.status)
    previous_status = incident.status
    incident.status = payload.status
    audit.record(
        db,
        actor=user.email,
        action=f"INCIDENT_STATUS_CHANGED_{previous_status}_TO_{payload.status}",
        target_resource=incident.incident_number,
        department_code=incident.department_code or user.department,
        reason=payload.reason,
    )
    await db.commit()
    return _to_read(incident)


@router.post("/{incident_id}/assign", response_model=IncidentRead)
async def assign_incident(
    incident_id: uuid.UUID,
    payload: IncidentAssign,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_permission("incident.assign")),
) -> IncidentRead:
    incident = await _load_or_404(db, incident_id)
    require_status(incident.status, "VERIFIED", "assign")
    incident.assigned_to = payload.assigned_to
    incident.status = "ASSIGNED"
    audit.record(
        db,
        actor=user.email,
        action=f"INCIDENT_ASSIGNED_TO_{payload.assigned_to}",
        target_resource=incident.incident_number,
        department_code=incident.department_code or user.department,
        reason=payload.reason,
    )
    await db.commit()
    return _to_read(incident)


@router.post("/{incident_id}/resolve", response_model=IncidentRead)
async def resolve_incident(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_permission("incident.resolve")),
) -> IncidentRead:
    incident = await _load_or_404(db, incident_id)
    require_status(incident.status, "RESPONDING", "resolve")
    now = datetime.now(UTC)
    incident.status = "RESOLVED"
    incident.resolved_at = now
    created_at = incident.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    incident.response_time_seconds = int((now - created_at).total_seconds())
    audit.record(
        db,
        actor=user.email,
        action="INCIDENT_RESOLVED",
        target_resource=incident.incident_number,
        department_code=incident.department_code or user.department,
    )
    await db.commit()
    return _to_read(incident)


# No DELETE endpoint: spec section 10 lists incidents as
# "Create, Read, Update, Resolve/archive" -- never hard-deleted, so the
# audit trail (`/resolve`, `/status`, `/assign`) always stays intact.
