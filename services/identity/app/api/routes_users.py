import math
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, require_permission
from app.core.errors import AppError
from app.core.security import hash_password
from app.db.models import Department, Role, User
from app.schemas.common import PageMeta
from app.schemas.user import UserCreate, UserListResponse, UserRead, UserUpdate

router = APIRouter(prefix="/api/v1/users", tags=["users"])


def _to_read(user: User) -> UserRead:
    return UserRead(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role_code=user.role.code,
        department_code=user.department.code if user.department else None,
        status=user.status,
        email_verified=user.email_verified_at is not None,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )


async def _load_role(db: AsyncSession, code: str) -> Role:
    role = await db.scalar(select(Role).where(Role.code == code))
    if role is None:
        raise AppError(400, "ROLE_NOT_FOUND", f"Role '{code}' does not exist.")
    return role


async def _load_department(db: AsyncSession, code: str | None) -> Department | None:
    if code is None:
        return None
    department = await db.scalar(select(Department).where(Department.code == code))
    if department is None:
        raise AppError(400, "DEPARTMENT_NOT_FOUND", f"Department '{code}' does not exist.")
    return department


async def _load_user_or_404(db: AsyncSession, user_id: uuid.UUID) -> User:
    user = await db.scalar(
        select(User)
        .options(selectinload(User.role), selectinload(User.department))
        .where(User.id == user_id)
    )
    if user is None:
        raise AppError(404, "USER_NOT_FOUND", "The requested user does not exist.")
    return user


@router.get(
    "", response_model=UserListResponse, dependencies=[Depends(require_permission("user.read"))]
)
async def list_users(
    db: AsyncSession = Depends(get_db),
    q: str | None = Query(default=None, description="Search by name or email"),
    status_filter: str | None = Query(default=None, alias="status"),
    department: str | None = Query(default=None),
    role: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> UserListResponse:
    stmt = select(User).options(selectinload(User.role), selectinload(User.department))
    if q:
        pattern = f"%{q.lower()}%"
        stmt = stmt.where(
            or_(func.lower(User.email).like(pattern), func.lower(User.full_name).like(pattern))
        )
    if status_filter:
        stmt = stmt.where(User.status == status_filter)
    if department:
        stmt = stmt.join(Department).where(Department.code == department)
    if role:
        stmt = stmt.join(Role).where(Role.code == role)

    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    stmt = stmt.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    users = (await db.scalars(stmt)).all()

    return UserListResponse(
        items=[_to_read(user) for user in users],
        meta=PageMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=max(1, math.ceil(total / page_size)),
        ),
    )


@router.get(
    "/{user_id}", response_model=UserRead, dependencies=[Depends(require_permission("user.read"))]
)
async def get_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> UserRead:
    return _to_read(await _load_user_or_404(db, user_id))


@router.post(
    "",
    response_model=UserRead,
    status_code=201,
    dependencies=[Depends(require_permission("user.create"))],
)
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> UserRead:
    email = payload.email.lower()
    if await db.scalar(select(User).where(User.email == email)):
        raise AppError(
            409, "EMAIL_ALREADY_REGISTERED", "An account with this email already exists."
        )
    role = await _load_role(db, payload.role_code)
    department = await _load_department(db, payload.department_code)
    user = User(
        email=email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role_id=role.id,
        department_id=department.id if department else None,
        status="ACTIVE",
    )
    db.add(user)
    await db.commit()
    return _to_read(await _load_user_or_404(db, user.id))


@router.patch(
    "/{user_id}", response_model=UserRead, dependencies=[Depends(require_permission("user.update"))]
)
async def update_user(
    user_id: uuid.UUID, payload: UserUpdate, db: AsyncSession = Depends(get_db)
) -> UserRead:
    user = await _load_user_or_404(db, user_id)
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.role_code is not None:
        user.role_id = (await _load_role(db, payload.role_code)).id
    if payload.department_code is not None:
        department = await _load_department(db, payload.department_code)
        user.department_id = department.id if department else None
    if payload.status is not None:
        user.status = payload.status
    await db.commit()
    return _to_read(await _load_user_or_404(db, user_id))


@router.delete(
    "/{user_id}", response_model=UserRead, dependencies=[Depends(require_permission("user.delete"))]
)
async def deactivate_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> UserRead:
    user = await _load_user_or_404(db, user_id)
    user.status = "DEACTIVATED"
    await db.commit()
    return _to_read(await _load_user_or_404(db, user_id))
