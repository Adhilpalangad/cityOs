import math
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_permission
from app.core.errors import AppError
from app.db.models import Hospital
from app.schemas.common import PageMeta
from app.schemas.hospitals import HospitalCreate, HospitalListResponse, HospitalRead, HospitalUpdate
from app.services.notifications import ICU_CAPACITY_ALERT_THRESHOLD, notify

router = APIRouter(prefix="/api/v1/hospitals", tags=["hospitals"])


def _to_read(hospital: Hospital) -> HospitalRead:
    return HospitalRead(
        id=str(hospital.id),
        code=hospital.code,
        name=hospital.name,
        latitude=hospital.latitude,
        longitude=hospital.longitude,
        beds_total=hospital.beds_total,
        beds_occupied=hospital.beds_occupied,
        icu_total=hospital.icu_total,
        icu_occupied=hospital.icu_occupied,
        emergency_capacity=hospital.emergency_capacity,
        status=hospital.status,
        created_at=hospital.created_at,
        updated_at=hospital.updated_at,
    )


async def _load_or_404(db: AsyncSession, hospital_id: uuid.UUID) -> Hospital:
    hospital = await db.get(Hospital, hospital_id)
    if hospital is None:
        raise AppError(404, "HOSPITAL_NOT_FOUND", "The requested hospital does not exist.")
    return hospital


@router.get(
    "",
    response_model=HospitalListResponse,
    dependencies=[Depends(require_permission("hospital.read"))],
)
async def list_hospitals(
    db: AsyncSession = Depends(get_db),
    q: str | None = Query(default=None, description="Search by code or name"),
    status_filter: str | None = Query(default=None, alias="status"),
    emergency_capacity: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> HospitalListResponse:
    stmt = select(Hospital)
    if q:
        pattern = f"%{q.lower()}%"
        stmt = stmt.where(
            or_(func.lower(Hospital.code).like(pattern), func.lower(Hospital.name).like(pattern))
        )
    if status_filter:
        stmt = stmt.where(Hospital.status == status_filter)
    if emergency_capacity:
        stmt = stmt.where(Hospital.emergency_capacity == emergency_capacity)

    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    stmt = stmt.order_by(Hospital.code).offset((page - 1) * page_size).limit(page_size)
    hospitals = (await db.scalars(stmt)).all()

    return HospitalListResponse(
        items=[_to_read(hospital) for hospital in hospitals],
        meta=PageMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=max(1, math.ceil(total / page_size)),
        ),
    )


@router.get(
    "/{hospital_id}",
    response_model=HospitalRead,
    dependencies=[Depends(require_permission("hospital.read"))],
)
async def get_hospital(hospital_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> HospitalRead:
    return _to_read(await _load_or_404(db, hospital_id))


@router.post(
    "",
    response_model=HospitalRead,
    status_code=201,
    dependencies=[Depends(require_permission("hospital.create"))],
)
async def create_hospital(
    payload: HospitalCreate, db: AsyncSession = Depends(get_db)
) -> HospitalRead:
    if await db.scalar(select(Hospital).where(Hospital.code == payload.code)):
        raise AppError(409, "HOSPITAL_ALREADY_EXISTS", f"Hospital '{payload.code}' already exists.")
    hospital = Hospital(
        code=payload.code,
        name=payload.name,
        latitude=payload.latitude,
        longitude=payload.longitude,
        beds_total=payload.beds_total,
        icu_total=payload.icu_total,
    )
    db.add(hospital)
    await db.commit()
    return _to_read(hospital)


@router.patch(
    "/{hospital_id}",
    response_model=HospitalRead,
    dependencies=[Depends(require_permission("hospital.update"))],
)
async def update_hospital(
    hospital_id: uuid.UUID, payload: HospitalUpdate, db: AsyncSession = Depends(get_db)
) -> HospitalRead:
    hospital = await _load_or_404(db, hospital_id)

    def _icu_ratio() -> float:
        return hospital.icu_occupied / hospital.icu_total if hospital.icu_total else 0.0

    was_over_threshold = _icu_ratio() >= ICU_CAPACITY_ALERT_THRESHOLD

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(hospital, field, value)
    if hospital.beds_occupied > hospital.beds_total:
        raise AppError(400, "INVALID_CAPACITY", "beds_occupied cannot exceed beds_total.")
    if hospital.icu_occupied > hospital.icu_total:
        raise AppError(400, "INVALID_CAPACITY", "icu_occupied cannot exceed icu_total.")

    # Spec section 48's third trigger rule: ICU capacity crossing a
    # threshold notifies Health Control. Fires once on the crossing, not on
    # every update while still over threshold.
    now_over_threshold = _icu_ratio() >= ICU_CAPACITY_ALERT_THRESHOLD
    if now_over_threshold and not was_over_threshold:
        notify(
            db,
            title=f"ICU capacity alert: {hospital.name}",
            message=(
                f"{hospital.name} ICU occupancy reached {hospital.icu_occupied}/"
                f"{hospital.icu_total} ({_icu_ratio():.0%})."
            ),
            severity="CRITICAL",
            target_department="HEALTHCARE",
        )

    await db.commit()
    return _to_read(hospital)


@router.delete(
    "/{hospital_id}", status_code=204, dependencies=[Depends(require_permission("hospital.delete"))]
)
async def delete_hospital(hospital_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> None:
    hospital = await _load_or_404(db, hospital_id)
    await db.delete(hospital)
    await db.commit()
