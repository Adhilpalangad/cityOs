from .helpers import create_user


async def _login(client, db, *, email: str, password: str, role_code: str, **kwargs) -> str:
    await create_user(db, email=email, password=password, role_code=role_code, **kwargs)
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_unauthenticated_request_is_rejected(client) -> None:
    response = client.get("/api/v1/users")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


async def test_citizen_cannot_list_users(client, db) -> None:
    token = await _login(
        client, db, email="citizen@example.com", password="correct-password-1", role_code="CITIZEN"
    )
    response = client.get("/api/v1/users", headers=_auth(token))
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"


async def test_traffic_officer_permissions_match_spec_example(client, db) -> None:
    token = await _login(
        client,
        db,
        email="officer@example.com",
        password="correct-password-1",
        role_code="TRAFFIC_OFFICER",
    )
    me = client.get("/api/v1/auth/me", headers=_auth(token))
    assert me.status_code == 200
    assert set(me.json()["permissions"]) == {
        "traffic.read",
        "traffic.update",
        "incident.create",
        "incident.read",
        "vehicle.read",
    }


async def test_super_admin_can_manage_users(client, db) -> None:
    token = await _login(
        client,
        db,
        email="admin@example.com",
        password="correct-password-1",
        role_code="SUPER_ADMIN",
    )

    listed = client.get("/api/v1/users", headers=_auth(token))
    assert listed.status_code == 200
    assert listed.json()["meta"]["total"] >= 1

    created = client.post(
        "/api/v1/users",
        headers=_auth(token),
        json={
            "email": "staff@example.com",
            "password": "correct-password-1",
            "full_name": "New Staff",
            "role_code": "TRAFFIC_OFFICER",
            "department_code": "TRAFFIC",
        },
    )
    assert created.status_code == 201
    user_id = created.json()["id"]
    assert created.json()["status"] == "ACTIVE"

    suspended = client.patch(
        f"/api/v1/users/{user_id}", headers=_auth(token), json={"status": "SUSPENDED"}
    )
    assert suspended.status_code == 200
    assert suspended.json()["status"] == "SUSPENDED"

    deactivated = client.delete(f"/api/v1/users/{user_id}", headers=_auth(token))
    assert deactivated.status_code == 200
    assert deactivated.json()["status"] == "DEACTIVATED"


async def test_super_admin_can_create_role_and_department(client, db) -> None:
    token = await _login(
        client,
        db,
        email="rbac-admin@example.com",
        password="correct-password-1",
        role_code="SUPER_ADMIN",
    )

    department = client.post(
        "/api/v1/departments",
        headers=_auth(token),
        json={"code": "PARKS", "name": "Parks & Recreation"},
    )
    assert department.status_code == 201

    role = client.post(
        "/api/v1/roles",
        headers=_auth(token),
        json={
            "code": "PARKS_OFFICER",
            "name": "Parks Officer",
            "department_code": "PARKS",
            "permissions": ["incident.read", "incident.create"],
        },
    )
    assert role.status_code == 201
    assert role.json()["permissions"] == ["incident.create", "incident.read"]


async def test_role_create_rejects_unknown_permission(client, db) -> None:
    token = await _login(
        client,
        db,
        email="rbac-admin-2@example.com",
        password="correct-password-1",
        role_code="SUPER_ADMIN",
    )
    response = client.post(
        "/api/v1/roles",
        headers=_auth(token),
        json={"code": "GHOST_ROLE", "name": "Ghost", "permissions": ["not.a.real.permission"]},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "PERMISSION_NOT_FOUND"
