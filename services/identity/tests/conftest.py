import os

# Must run before any `app.*` import: Settings is cached on first use, and
# app.db.base builds its engine at import time. A real DATABASE_URL/REDIS_URL
# already present in the environment (e.g. for an integration test run) is
# left untouched -- these are only fallback defaults for plain unit tests.
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:16399/0")  # deliberately unreachable
os.environ.setdefault("JWT_SECRET", "test-only-secret-that-is-at-least-32-bytes-long")
os.environ.setdefault("SUPERADMIN_EMAIL", "")
os.environ.setdefault("SUPERADMIN_PASSWORD", "")

from collections.abc import AsyncIterator, Iterator  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.api.deps import get_db  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.models import Department, Permission, Role  # noqa: E402
from app.db.seed_data import DEPARTMENTS, PERMISSIONS, ROLES, WILDCARD_PERMISSION  # noqa: E402
from app.main import app  # noqa: E402
from app.services import email  # noqa: E402


async def _seed_rbac(session: AsyncSession) -> None:
    departments = {code: Department(code=code, name=name) for code, name in DEPARTMENTS}
    session.add_all(departments.values())
    await session.flush()

    permissions = {
        code: Permission(code=code, description=description) for code, description in PERMISSIONS
    }
    session.add_all(permissions.values())
    await session.flush()

    for code, name, department_code, is_platform_role, permission_codes in ROLES:
        granted = (
            list(permissions.values())
            if permission_codes == [WILDCARD_PERMISSION]
            else [permissions[c] for c in permission_codes]
        )
        session.add(
            Role(
                code=code,
                name=name,
                department_id=departments[department_code].id if department_code else None,
                is_platform_role=is_platform_role,
                permissions=granted,
            )
        )
    await session.commit()


@pytest.fixture
async def session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as session:
        await _seed_rbac(session)

    yield factory
    await engine.dispose()


@pytest.fixture
async def db(session_factory: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncSession]:
    """A session tests can use directly, e.g. to plant a user with a specific role."""
    async with session_factory() as session:
        yield session


@pytest.fixture
def client(session_factory: async_sessionmaker[AsyncSession]) -> Iterator[TestClient]:
    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    email.OUTBOX.clear()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
