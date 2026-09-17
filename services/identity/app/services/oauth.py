"""Google and GitHub OAuth 2.0 authorization-code flows.

The redirect `state` parameter is a short-lived signed JWT rather than
server-side session state, so the identity service stays stateless and this
works behind any number of replicas without a shared store.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx
import jwt

from app.core.config import Settings
from app.core.errors import AppError

SUPPORTED_PROVIDERS = ("google", "github")


@dataclass
class OAuthProfile:
    provider: str
    provider_account_id: str
    email: str
    full_name: str


def _require_provider(provider: str) -> None:
    if provider not in SUPPORTED_PROVIDERS:
        raise AppError(404, "OAUTH_PROVIDER_UNKNOWN", f"Unknown OAuth provider '{provider}'.")


def _client_credentials(settings: Settings, provider: str) -> tuple[str, str]:
    client_id, client_secret = {
        "google": (settings.google_client_id, settings.google_client_secret),
        "github": (settings.github_client_id, settings.github_client_secret),
    }[provider]
    if not client_id or not client_secret:
        raise AppError(
            503,
            "OAUTH_NOT_CONFIGURED",
            f"{provider.capitalize()} OAuth is not configured on this deployment.",
        )
    return client_id, client_secret


def sign_state(settings: Settings, *, provider: str) -> str:
    now = datetime.now(UTC)
    claims = {
        "provider": provider,
        "type": "oauth_state",
        "iat": now,
        "exp": now + timedelta(minutes=10),
    }
    return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_state(settings: Settings, *, state: str, provider: str) -> None:
    try:
        claims = jwt.decode(state, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.InvalidTokenError as exc:
        raise AppError(
            400, "OAUTH_STATE_INVALID", "OAuth state is invalid or has expired."
        ) from exc
    if claims.get("type") != "oauth_state" or claims.get("provider") != provider:
        raise AppError(400, "OAUTH_STATE_INVALID", "OAuth state does not match this provider.")


def build_authorize_url(settings: Settings, *, provider: str) -> str:
    _require_provider(provider)
    client_id, _ = _client_credentials(settings, provider)
    redirect_uri = f"{settings.oauth_redirect_base_url}/api/v1/auth/oauth/{provider}/callback"
    state = sign_state(settings, provider=provider)
    if provider == "google":
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "online",
        }
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "read:user user:email",
        "state": state,
    }
    return f"https://github.com/login/oauth/authorize?{urlencode(params)}"


async def exchange_code(settings: Settings, *, provider: str, code: str) -> OAuthProfile:
    _require_provider(provider)
    client_id, client_secret = _client_credentials(settings, provider)
    redirect_uri = f"{settings.oauth_redirect_base_url}/api/v1/auth/oauth/{provider}/callback"
    async with httpx.AsyncClient(timeout=10) as client:
        if provider == "google":
            return await _exchange_google(client, client_id, client_secret, redirect_uri, code)
        return await _exchange_github(client, client_id, client_secret, redirect_uri, code)


async def _exchange_google(
    client: httpx.AsyncClient, client_id: str, client_secret: str, redirect_uri: str, code: str
) -> OAuthProfile:
    token_response = await client.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
    )
    _raise_if_failed(token_response, "google")
    access_token = token_response.json()["access_token"]
    profile_response = await client.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    _raise_if_failed(profile_response, "google")
    profile: dict[str, Any] = profile_response.json()
    return OAuthProfile(
        provider="google",
        provider_account_id=str(profile["sub"]),
        email=profile["email"],
        full_name=profile.get("name") or profile["email"],
    )


async def _exchange_github(
    client: httpx.AsyncClient, client_id: str, client_secret: str, redirect_uri: str, code: str
) -> OAuthProfile:
    token_response = await client.post(
        "https://github.com/login/oauth/access_token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
        },
        headers={"Accept": "application/json"},
    )
    _raise_if_failed(token_response, "github")
    access_token = token_response.json().get("access_token")
    if not access_token:
        raise AppError(502, "OAUTH_EXCHANGE_FAILED", "GitHub did not return an access token.")
    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json"}
    profile_response = await client.get("https://api.github.com/user", headers=headers)
    _raise_if_failed(profile_response, "github")
    profile: dict[str, Any] = profile_response.json()

    email = profile.get("email")
    if not email:
        emails_response = await client.get("https://api.github.com/user/emails", headers=headers)
        _raise_if_failed(emails_response, "github")
        primary = next(
            (e for e in emails_response.json() if e.get("primary") and e.get("verified")), None
        )
        email = primary["email"] if primary else None
    if not email:
        raise AppError(
            422, "OAUTH_EMAIL_UNAVAILABLE", "GitHub account has no accessible verified email."
        )

    return OAuthProfile(
        provider="github",
        provider_account_id=str(profile["id"]),
        email=email,
        full_name=profile.get("name") or profile.get("login") or email,
    )


def _raise_if_failed(response: httpx.Response, provider: str) -> None:
    if response.status_code >= 400:
        raise AppError(
            502, "OAUTH_EXCHANGE_FAILED", f"{provider.capitalize()} rejected the OAuth exchange."
        )
