"""Infrastructure Management (spec section 47: roads, bridges, buildings,
drainage, streetlights, ... condition, risk, cost, maintenance).

Replaces routes_extended.py's GET-only, self-seeded InfrastructureAsset
stub with real create/update endpoints. A condition or risk_level change is
audited (app/services/audit.py) -- spec section 47 lists both as the fields
an inspection updates, and a risk escalation on a bridge or drainage asset
is exactly the kind of action section 50 wants a paper trail for.

No DELETE: an asset being decommissioned is itself a fact worth keeping on
record, not something that should make the row disappear -- same reasoning
as incidents and workflow tasks.
"""

import math
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db, require_permission
from app.core.errors import AppError
from app.db.models import InfrastructureAsset
from app.schemas.common import PageMeta
from app.schemas.infrastructure import (
    InfrastructureAssetCreate,
    InfrastructureAssetListResponse,
    InfrastructureAssetRead,
    InfrastructureAssetUpdate,
)
from app.services import audit

router = APIRouter(prefix="/api/v1/infrastructure", tags=["infrastructure"])


def _to_read(asset: InfrastructureAsset) -> InfrastructureAssetRead:
    return InfrastructureAssetRead(
        id=str(asset.id),
        asset_code=asset.asset_code,
        name=asset.name,
        asset_type=asset.asset_type,
        department_code=asset.department_code,
        condition=asset.condition,
        risk_level=asset.risk_level,
        latitude=asset.latitude,
        longitude=asset.longitude,
        estimated_cost=asset.estimated_cost,
        next_maintenance=asset.next_maintenance,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


async def _load_or_404(db: AsyncSession, asset_id: uuid.UUID) -> InfrastructureAsset:
    asset = await db.get(InfrastructureAsset, asset_id)
    if asset is None:
        raise AppError(404, "ASSET_NOT_FOUND", "The requested infrastructure asset does not exist.")
    return asset


@router.get(
    "",
    response_model=InfrastructureAssetListResponse,
    dependencies=[Depends(require_permission("infrastructure.read"))],
)
async def list_infrastructure_assets(
    db: AsyncSession = Depends(get_db),
    q: str | None = Query(default=None, description="Search by asset code or name"),
    asset_type: str | None = Query(default=None),
    risk_level: str | None = Query(default=None),
    department_code: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> InfrastructureAssetListResponse:
    stmt = select(InfrastructureAsset)
    if q:
        pattern = f"%{q.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(InfrastructureAsset.asset_code).like(pattern),
                func.lower(InfrastructureAsset.name).like(pattern),
            )
        )
    if asset_type:
        stmt = stmt.where(InfrastructureAsset.asset_type == asset_type)
    if risk_level:
        stmt = stmt.where(InfrastructureAsset.risk_level == risk_level)
    if department_code:
        stmt = stmt.where(InfrastructureAsset.department_code == department_code)

    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    stmt = (
        stmt.order_by(InfrastructureAsset.asset_code.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    assets = (await db.scalars(stmt)).all()

    return InfrastructureAssetListResponse(
        items=[_to_read(a) for a in assets],
        meta=PageMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=max(1, math.ceil(total / page_size)),
        ),
    )


@router.get("/{asset_id}", response_model=InfrastructureAssetRead)
async def get_infrastructure_asset(
    asset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_permission("infrastructure.read")),
) -> InfrastructureAssetRead:
    return _to_read(await _load_or_404(db, asset_id))


@router.post("", response_model=InfrastructureAssetRead, status_code=201)
async def create_infrastructure_asset(
    payload: InfrastructureAssetCreate,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_permission("infrastructure.create")),
) -> InfrastructureAssetRead:
    if await db.scalar(
        select(InfrastructureAsset).where(InfrastructureAsset.asset_code == payload.asset_code)
    ):
        raise AppError(
            409, "ASSET_ALREADY_EXISTS", f"Asset '{payload.asset_code}' already exists."
        )
    asset = InfrastructureAsset(
        asset_code=payload.asset_code,
        name=payload.name,
        asset_type=payload.asset_type,
        department_code=payload.department_code,
        latitude=payload.latitude,
        longitude=payload.longitude,
        estimated_cost=payload.estimated_cost,
        next_maintenance=payload.next_maintenance,
    )
    db.add(asset)
    await db.commit()
    return _to_read(asset)


@router.patch("/{asset_id}", response_model=InfrastructureAssetRead)
async def update_infrastructure_asset(
    asset_id: uuid.UUID,
    payload: InfrastructureAssetUpdate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_permission("infrastructure.update")),
) -> InfrastructureAssetRead:
    asset = await _load_or_404(db, asset_id)
    data = payload.model_dump(exclude_unset=True)
    reason = data.pop("reason", None)

    previous_condition, previous_risk = asset.condition, asset.risk_level
    for field, value in data.items():
        setattr(asset, field, value)

    changes = []
    if "condition" in data and data["condition"] != previous_condition:
        changes.append(f"CONDITION_{previous_condition}_TO_{data['condition']}")
    if "risk_level" in data and data["risk_level"] != previous_risk:
        changes.append(f"RISK_{previous_risk}_TO_{data['risk_level']}")

    for change in changes:
        audit.record(
            db,
            actor=user.email,
            action=f"ASSET_{change}",
            target_resource=asset.asset_code,
            department_code=asset.department_code,
            reason=reason,
        )

    await db.commit()
    return _to_read(asset)
