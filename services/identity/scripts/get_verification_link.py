"""Dev helper: mint a fresh, usable email-verification link for an account.

Existing tokens are stored hashed (one-way), so there's no way to recover a
previously issued raw token -- this issues a brand new one instead, exactly
like `/api/v1/auth/resend-verification` does, and prints the link directly
instead of only logging that an email was "sent".

Usage (from services/identity):
    python -m scripts.get_verification_link user@example.com
"""

import asyncio
import sys
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import generate_opaque_token
from app.db.base import SessionLocal
from app.db.models import EmailVerificationToken, User


async def main(email: str) -> int:
    settings = get_settings()
    async with SessionLocal() as db:
        user = await db.scalar(select(User).where(User.email == email.lower()))
        if user is None:
            print(f"No account found for {email}.")
            return 1
        raw_token, token_hash = generate_opaque_token()
        db.add(
            EmailVerificationToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=datetime.now(UTC)
                + timedelta(hours=settings.email_verification_token_expire_hours),
            )
        )
        await db.commit()
        print(f"{settings.frontend_url}/verify-email?token={raw_token}")
        return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.get_verification_link <email>")
        sys.exit(1)
    sys.exit(asyncio.run(main(sys.argv[1])))
