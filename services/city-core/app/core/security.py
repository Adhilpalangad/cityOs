"""Access-token verification.

city-core never issues tokens -- only `identity` does. It verifies the same
HS256 JWTs using the shared `JWT_SECRET`, which is how every downstream
service in this platform authorizes requests without a database round trip
or a call back to identity. This module and `app/api/deps.py` are
intentionally a near-duplicate of identity's decode-side code: they are
small (well under a shared-package's worth of coupling), and every service
that only verifies -- never issues -- tokens should carry this same copy
rather than depend on identity's package, which also carries password
hashing, OAuth, and email concerns it doesn't need.
"""

from typing import Any

import jwt

from app.core.config import Settings


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
