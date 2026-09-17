"""Password hashing, JWT issuance, and opaque-token helpers.

Password storage uses Argon2id (`argon2-cffi`), the preferred algorithm called
out in the platform spec. Access tokens are short-lived JWTs carrying the
user's role, department, and resolved permission codes so downstream
permission checks are a single decode, not a database round trip; refresh,
email-verification, and password-reset tokens are opaque random strings and
only their SHA-256 hash is ever persisted, so a database leak does not expose
usable tokens.
"""

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import Settings

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def needs_rehash(password_hash: str) -> bool:
    return _hasher.check_needs_rehash(password_hash)


def generate_opaque_token() -> tuple[str, str]:
    """Return (raw_token, sha256_hash). Only the hash is persisted."""
    raw = secrets.token_urlsafe(32)
    return raw, hashlib.sha256(raw.encode("utf-8")).hexdigest()


def hash_opaque_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def create_access_token(
    settings: Settings,
    *,
    user_id: uuid.UUID,
    email: str,
    role_code: str,
    department_code: str | None,
    permissions: list[str],
) -> str:
    now = datetime.now(UTC)
    claims: dict[str, Any] = {
        "sub": str(user_id),
        "email": email,
        "role": role_code,
        "department": department_code,
        "permissions": permissions,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)


class TokenError(Exception):
    pass


def decode_access_token(settings: Settings, token: str) -> dict[str, Any]:
    try:
        claims = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError as exc:
        raise TokenError("Access token has expired.") from exc
    except jwt.InvalidTokenError as exc:
        raise TokenError("Access token is invalid.") from exc
    if claims.get("type") != "access":
        raise TokenError("Token is not an access token.")
    return claims
