import math
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_permission
from app.core.errors import AppError
from app.db.models import Road
from app.schemas.common import PageMeta
from app.schemas.roads import RoadCreate, RoadListResponse, RoadRead, RoadUpdate

router = APIRouter(prefix="/api/v1/roads", tags=["roads"])


def _to_read(road: Road) -> RoadRead:
    return RoadRead(
        id=str(road.id),
        code=road.code,
        name=road.name,
        road_type=road.road_type,
        status=road.status,
        capacity=road.capacity,
        current_vehicle_count=road.current_vehicle_count,
        average_speed_kmh=road.average_speed_kmh,
        traffic_level=road.traffic_level,
        risk_level=road.risk_level,
        waypoints=[tuple(point) for point in road.waypoints],
        created_at=road.created_at,
        updated_at=road.updated_at,
    )


async def _load_or_404(db: AsyncSession, road_id: uuid.UUID) -> Road:
    road = await db.get(Road, road_id)
    if road is None:
        raise AppError(404, "ROAD_NOT_FOUND", "The requested road does not exist.")
    return road


@router.get(
    "", response_model=RoadListResponse, dependencies=[Depends(require_permission("road.read"))]
)
async def list_roads(
    db: AsyncSession = Depends(get_db),
    q: str | None = Query(default=None, description="Search by code or name"),
    status_filter: str | None = Query(default=None, alias="status"),
    traffic_level: str | None = Query(default=None),
    risk_level: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> RoadListResponse:
    stmt = select(Road)
    if q:
        pattern = f"%{q.lower()}%"
        stmt = stmt.where(
            or_(func.lower(Road.code).like(pattern), func.lower(Road.name).like(pattern))
        )
    if status_filter:
        stmt = stmt.where(Road.status == status_filter)
    if traffic_level:
        stmt = stmt.where(Road.traffic_level == traffic_level)
    if risk_level:
        stmt = stmt.where(Road.risk_level == risk_level)

    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    stmt = stmt.order_by(Road.code).offset((page - 1) * page_size).limit(page_size)
    roads = (await db.scalars(stmt)).all()

    return RoadListResponse(
        items=[_to_read(road) for road in roads],
        meta=PageMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=max(1, math.ceil(total / page_size)),
        ),
    )


@router.get(
    "/{road_id}", response_model=RoadRead, dependencies=[Depends(require_permission("road.read"))]
)
async def get_road(road_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> RoadRead:
    return _to_read(await _load_or_404(db, road_id))


@router.post(
    "",
    response_model=RoadRead,
    status_code=201,
    dependencies=[Depends(require_permission("road.create"))],
)
async def create_road(payload: RoadCreate, db: AsyncSession = Depends(get_db)) -> RoadRead:
    if await db.scalar(select(Road).where(Road.code == payload.code)):
        raise AppError(409, "ROAD_ALREADY_EXISTS", f"Road '{payload.code}' already exists.")
    road = Road(
        code=payload.code,
        name=payload.name,
        road_type=payload.road_type,
        capacity=payload.capacity,
        waypoints=[list(point) for point in payload.waypoints],
    )
    db.add(road)
    await db.commit()
    return _to_read(road)


@router.patch(
    "/{road_id}", response_model=RoadRead, dependencies=[Depends(require_permission("road.update"))]
)
async def update_road(
    road_id: uuid.UUID, payload: RoadUpdate, db: AsyncSession = Depends(get_db)
) -> RoadRead:
    road = await _load_or_404(db, road_id)
    data = payload.model_dump(exclude_unset=True)
    if "waypoints" in data and data["waypoints"] is not None:
        data["waypoints"] = [list(point) for point in data["waypoints"]]
    for field, value in data.items():
        setattr(road, field, value)
    await db.commit()
    return _to_read(road)


@router.delete(
    "/{road_id}", status_code=204, dependencies=[Depends(require_permission("road.delete"))]
)
async def delete_road(road_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> None:
    road = await _load_or_404(db, road_id)
    await db.delete(road)
    await db.commit()
