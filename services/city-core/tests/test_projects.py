from sqlalchemy import select

from app.db.models import AuditLog

from .helpers import auth_headers

ALL = ["project.read", "project.create", "project.update"]


def _create_project(client, **overrides) -> dict:
    payload = {
        "project_code": "PRJ-2026-01",
        "name": "Smart Flood Resilience Upgrade",
        "department_code": "INFRASTRUCTURE",
        "budget": 100000.0,
    }
    payload.update(overrides)
    response = client.post("/api/v1/projects", headers=auth_headers(ALL), json=payload)
    assert response.status_code == 201
    return response.json()


def test_create_project_defaults(client) -> None:
    project = _create_project(client)
    assert project["status"] == "PLANNED"
    assert project["spent"] == 0.0
    assert project["variance_pct"] == 0.0


def test_create_project_rejects_duplicate_code(client) -> None:
    _create_project(client)
    response = client.post(
        "/api/v1/projects",
        headers=auth_headers(ALL),
        json={"project_code": "PRJ-2026-01", "name": "Dup", "department_code": "X"},
    )
    assert response.status_code == 409


def test_update_project_rejects_unknown_status(client) -> None:
    project = _create_project(client)
    response = client.patch(
        f"/api/v1/projects/{project['id']}", headers=auth_headers(ALL), json={"status": "ARCHIVED"}
    )
    assert response.status_code == 422


def test_update_project_rejects_completion_out_of_range(client) -> None:
    project = _create_project(client)
    response = client.patch(
        f"/api/v1/projects/{project['id']}",
        headers=auth_headers(ALL),
        json={"completion_percentage": 150},
    )
    assert response.status_code == 422


async def test_spend_within_budget_updates_totals_without_audit(client, db) -> None:
    project = _create_project(client)
    response = client.post(
        f"/api/v1/projects/{project['id']}/spend",
        headers=auth_headers(ALL),
        json={"amount": 40000.0},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["spent"] == 40000.0
    assert body["variance_pct"] == 40.0

    logs = (await db.scalars(select(AuditLog))).all()
    assert logs == []


async def test_spend_over_budget_writes_audit_entry_once(client, db) -> None:
    project = _create_project(client, budget=100000.0)

    client.post(
        f"/api/v1/projects/{project['id']}/spend",
        headers=auth_headers(ALL, email="finance@cityos.example", department="FINANCE"),
        json={"amount": 90000.0},
    )
    over = client.post(
        f"/api/v1/projects/{project['id']}/spend",
        headers=auth_headers(ALL, email="finance@cityos.example", department="FINANCE"),
        json={"amount": 20000.0},
    )
    assert over.status_code == 200
    assert over.json()["spent"] == 110000.0

    # A further spend, still over budget, shouldn't audit-log again -- only
    # the transition into overrun is the sensitive event.
    client.post(
        f"/api/v1/projects/{project['id']}/spend",
        headers=auth_headers(ALL, email="finance@cityos.example", department="FINANCE"),
        json={"amount": 5000.0},
    )

    logs = (await db.scalars(select(AuditLog))).all()
    assert len(logs) == 1
    assert logs[0].action == "PROJECT_BUDGET_OVERRUN"
    assert logs[0].actor == "finance@cityos.example"
    assert logs[0].target_resource == "PRJ-2026-01"


def test_spend_rejects_non_positive_amount(client) -> None:
    project = _create_project(client)
    response = client.post(
        f"/api/v1/projects/{project['id']}/spend", headers=auth_headers(ALL), json={"amount": 0}
    )
    assert response.status_code == 422


def test_project_has_no_delete_endpoint(client) -> None:
    project = _create_project(client)
    response = client.delete(f"/api/v1/projects/{project['id']}", headers=auth_headers(ALL))
    assert response.status_code == 405
