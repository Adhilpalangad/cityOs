"""Create the first SUPER_ADMIN account for a local/dev deployment.

RBAC has a chicken-and-egg problem: creating a user through the API
requires an existing user with `user.create`. This script breaks the cycle
by writing directly to the database. It is idempotent -- re-running it
once the account exists is a no-op -- and reads its inputs only from
environment variables so no credential is ever a command-line argument
(and therefore never lands in shell history).

Usage (from services/identity):
    SUPERADMIN_EMAIL=admin@cityos.example SUPERADMIN_PASSWORD=... \\
        python -m scripts.bootstrap_admin
"""

import asyncio
import sys
from datetime import UTC, datetime

from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.base import SessionLocal
from app.db.models import Role, User


async def main() -> int:
    settings = get_settings()
    if not settings.superadmin_email or not settings.superadmin_password:
        print("SUPERADMIN_EMAIL and SUPERADMIN_PASSWORD must both be set; skipping.")
        return 1

    email = settings.superadmin_email.lower()
    async with SessionLocal() as db:
        if await db.scalar(select(User).where(User.email == email)):
            print(f"{email} already exists; nothing to do.")
            return 0

        role = await db.scalar(select(Role).where(Role.code == "SUPER_ADMIN"))
        if role is None:
            print("SUPER_ADMIN role not found; run migrations first (`make migrate`).")
            return 1

        db.add(
            User(
                email=email,
                hashed_password=hash_password(settings.superadmin_password),
                full_name="Super Administrator",
                role_id=role.id,
                status="ACTIVE",
                email_verified_at=datetime.now(UTC),
            )
        )
        await db.commit()
        print(f"Created SUPER_ADMIN account for {email}.")
        return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
