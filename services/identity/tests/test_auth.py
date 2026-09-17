from urllib.parse import parse_qs, urlparse

from app.services import email

from .helpers import create_user


def _extract_token(body: str) -> str:
    link = body.split(": ", 1)[1].strip()
    return parse_qs(urlparse(link).query)["token"][0]


def test_register_login_and_me_flow(client) -> None:
    register = client.post(
        "/api/v1/auth/register",
        json={
            "email": "new.citizen@example.com",
            "password": "correct-horse-1",
            "full_name": "New Citizen",
        },
    )
    assert register.status_code == 201
    body = register.json()
    assert body["status"] == "PENDING_VERIFICATION"

    assert len(email.OUTBOX) == 1
    verification_token = _extract_token(email.OUTBOX[0]["body"])

    verify = client.post("/api/v1/auth/verify-email", json={"token": verification_token})
    assert verify.status_code == 200

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "new.citizen@example.com", "password": "correct-horse-1"},
    )
    assert login.status_code == 200
    tokens = login.json()
    assert tokens["token_type"] == "bearer"
    assert tokens["expires_in"] == 15 * 60

    me = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert me.status_code == 200
    me_body = me.json()
    assert me_body["email"] == "new.citizen@example.com"
    assert me_body["role"] == "CITIZEN"
    assert me_body["email_verified"] is True
    assert "complaint.create" in me_body["permissions"]


async def test_login_rejects_wrong_password(client, db) -> None:
    await create_user(
        db, email="known@example.com", password="correct-password-1", role_code="CITIZEN"
    )
    response = client.post(
        "/api/v1/auth/login", json={"email": "known@example.com", "password": "wrong-password"}
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


async def test_login_rejects_deactivated_account(client, db) -> None:
    await create_user(
        db,
        email="gone@example.com",
        password="correct-password-1",
        role_code="CITIZEN",
        status="DEACTIVATED",
    )
    response = client.post(
        "/api/v1/auth/login", json={"email": "gone@example.com", "password": "correct-password-1"}
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ACCOUNT_NOT_ACTIVE"


async def test_refresh_rotates_and_rejects_reuse(client, db) -> None:
    await create_user(
        db, email="rotate@example.com", password="correct-password-1", role_code="CITIZEN"
    )
    login = client.post(
        "/api/v1/auth/login", json={"email": "rotate@example.com", "password": "correct-password-1"}
    )
    first_refresh = login.json()["refresh_token"]

    refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": first_refresh})
    assert refreshed.status_code == 200
    assert refreshed.json()["refresh_token"] != first_refresh

    reused = client.post("/api/v1/auth/refresh", json={"refresh_token": first_refresh})
    assert reused.status_code == 401
    assert reused.json()["error"]["code"] == "TOKEN_INVALID"


async def test_logout_revokes_refresh_token(client, db) -> None:
    await create_user(
        db, email="logout@example.com", password="correct-password-1", role_code="CITIZEN"
    )
    login = client.post(
        "/api/v1/auth/login", json={"email": "logout@example.com", "password": "correct-password-1"}
    )
    refresh_token = login.json()["refresh_token"]

    logout = client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
    assert logout.status_code == 200

    refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refreshed.status_code == 401


async def test_password_reset_flow_revokes_existing_sessions(client, db) -> None:
    await create_user(db, email="reset@example.com", password="old-password-1", role_code="CITIZEN")
    login = client.post(
        "/api/v1/auth/login", json={"email": "reset@example.com", "password": "old-password-1"}
    )
    old_refresh_token = login.json()["refresh_token"]

    email.OUTBOX.clear()
    requested = client.post(
        "/api/v1/auth/request-password-reset", json={"email": "reset@example.com"}
    )
    assert requested.status_code == 202
    reset_token = _extract_token(email.OUTBOX[0]["body"])

    reset = client.post(
        "/api/v1/auth/reset-password", json={"token": reset_token, "new_password": "new-password-1"}
    )
    assert reset.status_code == 200

    # The refresh token issued before the reset must no longer work.
    stale = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh_token})
    assert stale.status_code == 401

    relogin = client.post(
        "/api/v1/auth/login", json={"email": "reset@example.com", "password": "new-password-1"}
    )
    assert relogin.status_code == 200


def test_register_rejects_duplicate_email(client) -> None:
    payload = {"email": "dup@example.com", "password": "correct-horse-1", "full_name": "Dup"}
    first = client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201
    second = client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "EMAIL_ALREADY_REGISTERED"


def test_register_rejects_weak_password(client) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "weak@example.com", "password": "short", "full_name": "Weak"},
    )
    assert response.status_code == 422


def test_oauth_authorize_without_configuration_is_unavailable(client) -> None:
    response = client.get("/api/v1/auth/oauth/google/authorize", follow_redirects=False)
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "OAUTH_NOT_CONFIGURED"


def test_oauth_authorize_rejects_unknown_provider(client) -> None:
    response = client.get("/api/v1/auth/oauth/facebook/authorize", follow_redirects=False)
    assert response.status_code == 404
