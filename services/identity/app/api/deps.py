"""Shared FastAPI dependencies: DB session, current-user resolution, RBAC.

The access token carries the resolved permission set at issuance time (see
`app.core.security.create_access_token`), so authorization here is a pure
JWT decode with no database round trip. That keeps every protected request
to a single hop but means a role/permission change takes effect on a
user's next login or token refresh, not mid-session -- an intentional
trade-off given the 15-minute access token lifetime.
"""

from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.core.security import TokenError, decode_access_token
from app.db.base import get_db as get_db

__all__ = ["get_db", "get_current_user", "require_permission", "CurrentUser"]

_bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    id: str
    email: str
    role: str
    department: str | None
    permissions: list[str]


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> CurrentUser:
    if credentials is None:
        raise AppError(401, "UNAUTHENTICATED", "An access token is required.")
    try:
        claims = decode_access_token(settings, credentials.credentials)
    except TokenError as exc:
        raise AppError(401, "TOKEN_INVALID", str(exc)) from exc
    return CurrentUser(
        id=claims["sub"],
        email=claims["email"],
        role=claims["role"],
        department=claims.get("department"),
        permissions=claims.get("permissions", []),
    )


def require_permission(code: str) -> Callable[..., CurrentUser]:
    async def dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if code not in user.permissions:
            raise AppError(
                403, "PERMISSION_DENIED", f"This action requires the '{code}' permission."
            )
        return user

    return dependency
