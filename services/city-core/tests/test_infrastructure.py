from sqlalchemy import select

from app.db.models import AuditLog

from .helpers import auth_headers

ALL = ["infrastructure.read", "infrastructure.create", "infrastructure.update"]


def _create_asset(client, **overrides) -> dict:
    payload = {
        "asset_code": "INF-BR-04",
        "name": "Harbor Suspension Bridge",
        "asset_type": "Bridge",
        "latitude": 9.9816,
        "longitude": 76.2999,
        "estimated_cost": 15000000.0,
    }
    payload.update(overrides)
    response = client.post("/api/v1/infrastructure", headers=auth_headers(ALL), json=payload)
    assert response.status_code == 201
    return response.json()


def test_create_infrastructure_asset_defaults(client) -> None:
    asset = _create_asset(client)
    assert asset["condition"] == "GOOD"
    assert asset["risk_level"] == "LOW"
    assert asset["department_code"] == "INFRASTRUCTURE"


def test_create_infrastructure_asset_rejects_duplicate_code(client) -> None:
    _create_asset(client)
    response = client.post(
        "/api/v1/infrastructure",
        headers=auth_headers(ALL),
        json={"asset_code": "INF-BR-04", "name": "Dup", "asset_type": "Bridge"},
    )
    assert response.status_code == 409


def test_update_infrastructure_asset_rejects_unknown_condition(client) -> None:
    asset = _create_asset(client)
    response = client.patch(
        f"/api/v1/infrastructure/{asset['id']}",
        headers=auth_headers(ALL),
        json={"condition": "DEMOLISHED"},
    )
    assert response.status_code == 422


async def test_condition_and_risk_change_write_audit_entries(client, db) -> None:
    asset = _create_asset(client)
    response = client.patch(
        f"/api/v1/infrastructure/{asset['id']}",
        headers=auth_headers(ALL, email="inspector@cityos.example", department="INFRASTRUCTURE"),
        json={"condition": "POOR", "risk_level": "HIGH", "reason": "Corrosion found on inspection"},
    )
    assert response.status_code == 200
    assert response.json()["condition"] == "POOR"

    logs = (await db.scalars(select(AuditLog))).all()
    actions = [log.action for log in logs]
    assert "ASSET_CONDITION_GOOD_TO_POOR" in actions
    assert "ASSET_RISK_LOW_TO_HIGH" in actions
    assert all(log.reason == "Corrosion found on inspection" for log in logs)
    assert all(log.actor == "inspector@cityos.example" for log in logs)


async def test_update_without_condition_or_risk_change_does_not_write_audit_entry(
    client, db
) -> None:
    asset = _create_asset(client)
    response = client.patch(
        f"/api/v1/infrastructure/{asset['id']}",
        headers=auth_headers(ALL),
        json={"estimated_cost": 16000000.0},
    )
    assert response.status_code == 200

    logs = (await db.scalars(select(AuditLog))).all()
    assert logs == []


def test_infrastructure_asset_has_no_delete_endpoint(client) -> None:
    asset = _create_asset(client)
    response = client.delete(f"/api/v1/infrastructure/{asset['id']}", headers=auth_headers(ALL))
    assert response.status_code == 405
