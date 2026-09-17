from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_permission
from app.core.errors import AppError
from app.db.models import Department, Role
from app.schemas.rbac import DepartmentCreate, DepartmentRead, DepartmentUpdate

router = APIRouter(prefix="/api/v1/departments", tags=["departments"])


def _to_read(department: Department) -> DepartmentRead:
    return DepartmentRead(code=department.code, name=department.name)


async def _load_or_404(db: AsyncSession, code: str) -> Department:
    department = await db.scalar(select(Department).where(Department.code == code))
    if department is None:
        raise AppError(404, "DEPARTMENT_NOT_FOUND", f"Department '{code}' does not exist.")
    return department


@router.get(
    "",
    response_model=list[DepartmentRead],
    dependencies=[Depends(require_permission("department.read"))],
)
async def list_departments(db: AsyncSession = Depends(get_db)) -> list[DepartmentRead]:
    departments = (await db.scalars(select(Department).order_by(Department.name))).all()
    return [_to_read(department) for department in departments]


@router.post(
    "",
    response_model=DepartmentRead,
    status_code=201,
    dependencies=[Depends(require_permission("department.create"))],
)
async def create_department(
    payload: DepartmentCreate, db: AsyncSession = Depends(get_db)
) -> DepartmentRead:
    if await db.scalar(select(Department).where(Department.code == payload.code)):
        raise AppError(
            409, "DEPARTMENT_ALREADY_EXISTS", f"Department '{payload.code}' already exists."
        )
    department = Department(code=payload.code, name=payload.name)
    db.add(department)
    await db.commit()
    return _to_read(department)


@router.patch(
    "/{code}",
    response_model=DepartmentRead,
    dependencies=[Depends(require_permission("department.update"))],
)
async def update_department(
    code: str, payload: DepartmentUpdate, db: AsyncSession = Depends(get_db)
) -> DepartmentRead:
    department = await _load_or_404(db, code)
    department.name = payload.name
    await db.commit()
    return _to_read(department)


@router.delete(
    "/{code}", status_code=204, dependencies=[Depends(require_permission("department.delete"))]
)
async def delete_department(code: str, db: AsyncSession = Depends(get_db)) -> None:
    department = await _load_or_404(db, code)
    if await db.scalar(select(Role.id).where(Role.department_id == department.id).limit(1)):
        raise AppError(409, "DEPARTMENT_IN_USE", "This department still has roles assigned to it.")
    await db.delete(department)
    await db.commit()
