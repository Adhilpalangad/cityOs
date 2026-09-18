"""Finance and Projects (spec section 46: budgets, spending, project
progress, variance).

Replaces routes_extended.py's GET-only, self-seeded CityProject stub with
real create/update/spend endpoints. A spend that pushes the project over
its budget is audited (app/services/audit.py) -- an overrun is exactly the
kind of financial event section 22/50 wants a department able to review.

No DELETE: a project's financial history shouldn't be able to disappear.
"""

import math
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db, require_permission
from app.core.errors import AppError
from app.db.models import CityProject
from app.schemas.common import PageMeta
from app.schemas.projects import (
    CityProjectCreate,
    CityProjectListResponse,
    CityProjectRead,
    CityProjectSpend,
    CityProjectUpdate,
)
from app.services import audit

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


def _to_read(project: CityProject) -> CityProjectRead:
    return CityProjectRead(
        id=str(project.id),
        project_code=project.project_code,
        name=project.name,
        department_code=project.department_code,
        budget=project.budget,
        spent=project.spent,
        status=project.status,
        completion_percentage=project.completion_percentage,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


async def _load_or_404(db: AsyncSession, project_id: uuid.UUID) -> CityProject:
    project = await db.get(CityProject, project_id)
    if project is None:
        raise AppError(404, "PROJECT_NOT_FOUND", "The requested project does not exist.")
    return project


@router.get(
    "",
    response_model=CityProjectListResponse,
    dependencies=[Depends(require_permission("project.read"))],
)
async def list_city_projects(
    db: AsyncSession = Depends(get_db),
    q: str | None = Query(default=None, description="Search by project code or name"),
    status_filter: str | None = Query(default=None, alias="status"),
    department_code: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> CityProjectListResponse:
    stmt = select(CityProject)
    if q:
        pattern = f"%{q.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(CityProject.project_code).like(pattern),
                func.lower(CityProject.name).like(pattern),
            )
        )
    if status_filter:
        stmt = stmt.where(CityProject.status == status_filter)
    if department_code:
        stmt = stmt.where(CityProject.department_code == department_code)

    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    stmt = (
        stmt.order_by(CityProject.project_code.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    projects = (await db.scalars(stmt)).all()

    return CityProjectListResponse(
        items=[_to_read(p) for p in projects],
        meta=PageMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=max(1, math.ceil(total / page_size)),
        ),
    )


@router.get("/{project_id}", response_model=CityProjectRead)
async def get_city_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_permission("project.read")),
) -> CityProjectRead:
    return _to_read(await _load_or_404(db, project_id))


@router.post("", response_model=CityProjectRead, status_code=201)
async def create_city_project(
    payload: CityProjectCreate,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_permission("project.create")),
) -> CityProjectRead:
    if await db.scalar(select(CityProject).where(CityProject.project_code == payload.project_code)):
        raise AppError(
            409, "PROJECT_ALREADY_EXISTS", f"Project '{payload.project_code}' already exists."
        )
    project = CityProject(
        project_code=payload.project_code,
        name=payload.name,
        department_code=payload.department_code,
        budget=payload.budget,
        status="PLANNED",
    )
    db.add(project)
    await db.commit()
    return _to_read(project)


@router.patch("/{project_id}", response_model=CityProjectRead)
async def update_city_project(
    project_id: uuid.UUID,
    payload: CityProjectUpdate,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_permission("project.update")),
) -> CityProjectRead:
    project = await _load_or_404(db, project_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    await db.commit()
    return _to_read(project)


@router.post("/{project_id}/spend", response_model=CityProjectRead)
async def record_city_project_spend(
    project_id: uuid.UUID,
    payload: CityProjectSpend,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_permission("project.update")),
) -> CityProjectRead:
    project = await _load_or_404(db, project_id)
    was_over_budget = project.spent > project.budget
    project.spent += payload.amount
    now_over_budget = project.spent > project.budget

    if now_over_budget and not was_over_budget:
        default_reason = (
            f"Spend of {payload.amount} pushed total spent ({project.spent}) "
            f"over budget ({project.budget})."
        )
        audit.record(
            db,
            actor=user.email,
            action="PROJECT_BUDGET_OVERRUN",
            target_resource=project.project_code,
            department_code=project.department_code,
            reason=payload.reason or default_reason,
        )

    await db.commit()
    return _to_read(project)
