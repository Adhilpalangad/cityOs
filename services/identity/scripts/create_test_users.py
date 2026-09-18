"""One-off dev helper: create a handful of known-credential test accounts.

Not part of the app -- run manually against a local/dev database only, the
same way scripts/bootstrap_admin.py is. Writes directly via the ORM (same
approach bootstrap_admin.py uses) rather than through the API, so it works
regardless of what's happening at the HTTP layer.

Usage (from services/identity):
    python -m scripts.create_test_users
"""

import asyncio
import sys
from datetime import UTC, datetime

from sqlalchemy import select

from app.core.security import hash_password
from app.db.base import SessionLocal
from app.db.models import Role, User

TEST_PASSWORD = "CityOS2026!"

# (email, role code, full name)
TEST_USERS = [
    ("test.admin@cityos.example", "SUPER_ADMIN", "Test Super Admin"),
    ("test.officer@cityos.example", "TRAFFIC_OFFICER", "Test Traffic Officer"),
    ("test.dispatcher@cityos.example", "DISPATCHER", "Test Emergency Dispatcher"),
    ("test.citizen@cityos.example", "CITIZEN", "Test Citizen"),
]


async def main() -> int:
    async with SessionLocal() as db:
        for email, role_code, full_name in TEST_USERS:
            email = email.lower()
            existing = await db.scalar(select(User).where(User.email == email))
            if existing:
                print(f"{email} already exists; skipping.")
                continue

            role = await db.scalar(select(Role).where(Role.code == role_code))
            if role is None:
                print(f"Role {role_code} not found -- skipping {email}.")
                continue

            db.add(
                User(
                    email=email,
                    hashed_password=hash_password(TEST_PASSWORD),
                    full_name=full_name,
                    role_id=role.id,
                    status="ACTIVE",
                    email_verified_at=datetime.now(UTC),
                )
            )
            print(f"Created {email} ({role_code}).")
        await db.commit()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
