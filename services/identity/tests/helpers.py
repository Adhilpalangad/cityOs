from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.models import Department, Role, User


async def create_user(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    role_code: str,
    full_name: str = "Test User",
    status: str = "ACTIVE",
    department_code: str | None = None,
) -> User:
    role = await db.scalar(select(Role).where(Role.code == role_code))
    assert role is not None, f"seed fixture is missing role {role_code}"
    department = None
    if department_code is not None:
        department = await db.scalar(select(Department).where(Department.code == department_code))
        assert department is not None, f"seed fixture is missing department {department_code}"
    user = User(
        email=email.lower(),
        hashed_password=hash_password(password),
        full_name=full_name,
        role_id=role.id,
        department_id=department.id if department else None,
        status=status,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
