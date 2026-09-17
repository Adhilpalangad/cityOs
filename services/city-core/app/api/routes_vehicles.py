import math
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_permission
from app.core.errors import AppError
from app.db.models import Vehicle
from app.schemas.common import PageMeta
from app.schemas.vehicles import (
    VehicleCreate,
    VehicleListResponse,
    VehiclePositionUpdate,
    VehicleRead,
    VehicleUpdate,
)

router = APIRouter(prefix="/api/v1/vehicles", tags=["vehicles"])


def _to_read(vehicle: Vehicle) -> VehicleRead:
    return VehicleRead(
        id=str(vehicle.id),
        vehicle_id=vehicle.vehicle_id,
        vehicle_type=vehicle.vehicle_type,
        status=vehicle.status,
        latitude=vehicle.latitude,
        longitude=vehicle.longitude,
        speed_kmh=vehicle.speed_kmh,
        heading_degrees=vehicle.heading_degrees,
        position_updated_at=vehicle.position_updated_at,
        created_at=vehicle.created_at,
        updated_at=vehicle.updated_at,
    )


async def _load_or_404(db: AsyncSession, vehicle_id: uuid.UUID) -> Vehicle:
    vehicle = await db.get(Vehicle, vehicle_id)
    if vehicle is None:
        raise AppError(404, "VEHICLE_NOT_FOUND", "The requested vehicle does not exist.")
    return vehicle


@router.get(
    "",
    response_model=VehicleListResponse,
    dependencies=[Depends(require_permission("vehicle.read"))],
)
async def list_vehicles(
    db: AsyncSession = Depends(get_db),
    q: str | None = Query(default=None, description="Search by vehicle_id"),
    vehicle_type: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> VehicleListResponse:
    stmt = select(Vehicle)
    if q:
        stmt = stmt.where(func.lower(Vehicle.vehicle_id).like(f"%{q.lower()}%"))
    if vehicle_type:
        stmt = stmt.where(Vehicle.vehicle_type == vehicle_type)
    if status_filter:
        stmt = stmt.where(Vehicle.status == status_filter)

    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    stmt = stmt.order_by(Vehicle.vehicle_id).offset((page - 1) * page_size).limit(page_size)
    vehicles = (await db.scalars(stmt)).all()

    return VehicleListResponse(
        items=[_to_read(vehicle) for vehicle in vehicles],
        meta=PageMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=max(1, math.ceil(total / page_size)),
        ),
    )


@router.get(
    "/{vehicle_id}",
    response_model=VehicleRead,
    dependencies=[Depends(require_permission("vehicle.read"))],
)
async def get_vehicle(vehicle_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> VehicleRead:
    return _to_read(await _load_or_404(db, vehicle_id))


@router.post(
    "",
    response_model=VehicleRead,
    status_code=201,
    dependencies=[Depends(require_permission("vehicle.create"))],
)
async def create_vehicle(payload: VehicleCreate, db: AsyncSession = Depends(get_db)) -> VehicleRead:
    if await db.scalar(select(Vehicle).where(Vehicle.vehicle_id == payload.vehicle_id)):
        raise AppError(
            409, "VEHICLE_ALREADY_EXISTS", f"Vehicle '{payload.vehicle_id}' already exists."
        )
    vehicle = Vehicle(vehicle_id=payload.vehicle_id, vehicle_type=payload.vehicle_type)
    db.add(vehicle)
    await db.commit()
    return _to_read(vehicle)


@router.patch(
    "/{vehicle_id}",
    response_model=VehicleRead,
    dependencies=[Depends(require_permission("vehicle.update"))],
)
async def update_vehicle(
    vehicle_id: uuid.UUID, payload: VehicleUpdate, db: AsyncSession = Depends(get_db)
) -> VehicleRead:
    vehicle = await _load_or_404(db, vehicle_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(vehicle, field, value)
    await db.commit()
    return _to_read(vehicle)


@router.put(
    "/{vehicle_id}/position",
    response_model=VehicleRead,
    dependencies=[Depends(require_permission("vehicle.update"))],
)
async def update_vehicle_position(
    vehicle_id: uuid.UUID, payload: VehiclePositionUpdate, db: AsyncSession = Depends(get_db)
) -> VehicleRead:
    """Accepts a position event in the shape a Vehicle Data Provider emits (spec section 14)."""
    vehicle = await _load_or_404(db, vehicle_id)
    vehicle.latitude = payload.latitude
    vehicle.longitude = payload.longitude
    vehicle.speed_kmh = payload.speed_kmh
    vehicle.heading_degrees = payload.heading_degrees
    vehicle.position_updated_at = datetime.now(UTC)
    await db.commit()
    return _to_read(vehicle)


@router.delete(
    "/{vehicle_id}", status_code=204, dependencies=[Depends(require_permission("vehicle.delete"))]
)
async def delete_vehicle(vehicle_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> None:
    vehicle = await _load_or_404(db, vehicle_id)
    await db.delete(vehicle)
    await db.commit()
