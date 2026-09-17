import uuid
from datetime import UTC, datetime, timedelta

import jwt

from app.core.config import get_settings


def make_token(
    permissions: list[str],
    *,
    role: str = "TEST_ROLE",
    department: str | None = None,
    email: str = "test@example.com",
) -> str:
    """Mint an access token shaped exactly like one identity would issue.

    city-core has no users of its own, so tests exercise permission
    enforcement by signing a token directly with the same shared
    JWT_SECRET the app reads -- there's no need to run identity's
    register/login flow just to test that `require_permission` works.
    """
    settings = get_settings()
    now = datetime.now(UTC)
    claims = {
        "sub": str(uuid.uuid4()),
        "email": email,
        "role": role,
        "department": department,
        "permissions": permissions,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=15),
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def auth_headers(permissions: list[str], **kwargs) -> dict[str, str]:
    return {"Authorization": f"Bearer {make_token(permissions, **kwargs)}"}
