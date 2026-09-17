from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, require_permission
from app.core.errors import AppError
from app.db.models import Department, Permission, Role, User
from app.schemas.rbac import RoleCreate, RoleRead, RoleUpdate

router = APIRouter(prefix="/api/v1/roles", tags=["roles"])


def _to_read(role: Role) -> RoleRead:
    return RoleRead(
        code=role.code,
        name=role.name,
        department_code=role.department.code if role.department else None,
        is_platform_role=role.is_platform_role,
        permissions=sorted(p.code for p in role.permissions),
    )


async def _load_role_or_404(db: AsyncSession, code: str) -> Role:
    role = await db.scalar(
        select(Role)
        .options(selectinload(Role.permissions), selectinload(Role.department))
        .where(Role.code == code)
    )
    if role is None:
        raise AppError(404, "ROLE_NOT_FOUND", f"Role '{code}' does not exist.")
    return role


async def _load_permissions(db: AsyncSession, codes: list[str]) -> list[Permission]:
    if not codes:
        return []
    permissions = (await db.scalars(select(Permission).where(Permission.code.in_(codes)))).all()
    found = {p.code for p in permissions}
    missing = set(codes) - found
    if missing:
        raise AppError(400, "PERMISSION_NOT_FOUND", f"Unknown permission codes: {sorted(missing)}")
    return list(permissions)


@router.get(
    "", response_model=list[RoleRead], dependencies=[Depends(require_permission("role.read"))]
)
async def list_roles(db: AsyncSession = Depends(get_db)) -> list[RoleRead]:
    roles = (
        await db.scalars(
            select(Role).options(selectinload(Role.permissions), selectinload(Role.department))
        )
    ).all()
    return [_to_read(role) for role in roles]


@router.get(
    "/{code}", response_model=RoleRead, dependencies=[Depends(require_permission("role.read"))]
)
async def get_role(code: str, db: AsyncSession = Depends(get_db)) -> RoleRead:
    return _to_read(await _load_role_or_404(db, code))


@router.post(
    "",
    response_model=RoleRead,
    status_code=201,
    dependencies=[Depends(require_permission("role.create"))],
)
async def create_role(payload: RoleCreate, db: AsyncSession = Depends(get_db)) -> RoleRead:
    if await db.scalar(select(Role).where(Role.code == payload.code)):
        raise AppError(409, "ROLE_ALREADY_EXISTS", f"Role '{payload.code}' already exists.")
    department = None
    if payload.department_code is not None:
        department = await db.scalar(
            select(Department).where(Department.code == payload.department_code)
        )
        if department is None:
            raise AppError(
                400,
                "DEPARTMENT_NOT_FOUND",
                f"Department '{payload.department_code}' does not exist.",
            )
    role = Role(
        code=payload.code,
        name=payload.name,
        department_id=department.id if department else None,
        permissions=await _load_permissions(db, payload.permissions),
    )
    db.add(role)
    await db.commit()
    return _to_read(await _load_role_or_404(db, role.code))


@router.patch(
    "/{code}", response_model=RoleRead, dependencies=[Depends(require_permission("role.update"))]
)
async def update_role(
    code: str, payload: RoleUpdate, db: AsyncSession = Depends(get_db)
) -> RoleRead:
    role = await _load_role_or_404(db, code)
    if payload.name is not None:
        role.name = payload.name
    if payload.department_code is not None:
        department = await db.scalar(
            select(Department).where(Department.code == payload.department_code)
        )
        if department is None:
            raise AppError(
                400,
                "DEPARTMENT_NOT_FOUND",
                f"Department '{payload.department_code}' does not exist.",
            )
        role.department_id = department.id
    if payload.permissions is not None:
        role.permissions = await _load_permissions(db, payload.permissions)
    await db.commit()
    return _to_read(await _load_role_or_404(db, code))


@router.delete(
    "/{code}",
    response_model=None,
    status_code=204,
    dependencies=[Depends(require_permission("role.delete"))],
)
async def delete_role(code: str, db: AsyncSession = Depends(get_db)) -> None:
    role = await _load_role_or_404(db, code)
    if role.is_platform_role:
        raise AppError(400, "ROLE_NOT_DELETABLE", "Platform roles cannot be deleted.")
    if await db.scalar(select(User.id).where(User.role_id == role.id).limit(1)):
        raise AppError(409, "ROLE_IN_USE", "This role is still assigned to one or more users.")
    await db.delete(role)
    await db.commit()
