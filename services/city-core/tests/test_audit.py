"""Tests that sensitive actions actually write an AuditLog row (spec section
50), via app/services/audit.py. Before this existed, the only AuditLog rows
ever created were two examples GET /api/v1/audit seeded once on first call
-- nothing in the system wrote a real entry.

Requests go through `client` (HTTP, exercises the whole route including
permission checks); `db` reads back what actually landed. Both fixtures
share the same underlying in-memory SQLite engine (see tests/conftest.py's
`session_factory`), so this is checking the real persisted result, not a
mock.
"""

from sqlalchemy import select

from app.db.models import AuditLog

from .helpers import auth_headers

ROAD_PERMS = ["road.read", "road.create", "road.update"]
INCIDENT_PERMS = [
    "incident.read", "incident.create", "incident.update", "incident.assign", "incident.resolve",
]


async def test_road_status_change_writes_audit_entry(client, db) -> None:
    created = client.post(
        "/api/v1/roads",
        headers=auth_headers(ROAD_PERMS),
        json={"code": "ROAD-900", "name": "Test Road", "capacity": 500},
    )
    assert created.status_code == 201
    road_id = created.json()["id"]

    updated = client.patch(
        f"/api/v1/roads/{road_id}",
        headers=auth_headers(ROAD_PERMS, email="officer@cityos.example", department="TRAFFIC"),
        json={"status": "CLOSED", "reason": "Emergency maintenance"},
    )
    assert updated.status_code == 200

    logs = (await db.scalars(select(AuditLog))).all()
    assert len(logs) == 1
    assert logs[0].actor == "officer@cityos.example"
    assert logs[0].action == "ROAD_STATUS_CHANGED_OPEN_TO_CLOSED"
    assert logs[0].target_resource == "ROAD-900"
    assert logs[0].department_code == "TRAFFIC"
    assert logs[0].reason == "Emergency maintenance"


async def test_road_update_without_status_change_does_not_write_audit_entry(client, db) -> None:
    created = client.post(
        "/api/v1/roads",
        headers=auth_headers(ROAD_PERMS),
        json={"code": "ROAD-901", "name": "Test Road", "capacity": 500},
    )
    road_id = created.json()["id"]

    updated = client.patch(
        f"/api/v1/roads/{road_id}",
        headers=auth_headers(ROAD_PERMS),
        json={"name": "Renamed Road"},
    )
    assert updated.status_code == 200

    logs = (await db.scalars(select(AuditLog))).all()
    assert logs == []


async def test_incident_lifecycle_writes_audit_entries(client, db) -> None:
    created = client.post(
        "/api/v1/incidents",
        headers=auth_headers(INCIDENT_PERMS),
        json={"incident_type": "ROAD_ACCIDENT", "severity": "CRITICAL"},
    )
    incident_id = created.json()["id"]
    incident_number = created.json()["incident_number"]

    client.patch(
        f"/api/v1/incidents/{incident_id}/status",
        headers=auth_headers(INCIDENT_PERMS),
        json={"status": "VERIFIED"},
    )
    client.post(
        f"/api/v1/incidents/{incident_id}/assign",
        headers=auth_headers(INCIDENT_PERMS),
        json={"assigned_to": "AMB-17", "reason": "Nearest available unit"},
    )
    client.patch(
        f"/api/v1/incidents/{incident_id}/status",
        headers=auth_headers(INCIDENT_PERMS),
        json={"status": "RESPONDING"},
    )
    client.post(f"/api/v1/incidents/{incident_id}/resolve", headers=auth_headers(INCIDENT_PERMS))

    logs = (await db.scalars(select(AuditLog).order_by(AuditLog.timestamp))).all()
    actions = [log.action for log in logs]
    assert "INCIDENT_STATUS_CHANGED_DETECTED_TO_VERIFIED" in actions
    assert "INCIDENT_ASSIGNED_TO_AMB-17" in actions
    assert "INCIDENT_STATUS_CHANGED_ASSIGNED_TO_RESPONDING" in actions
    assert "INCIDENT_RESOLVED" in actions
    assert all(log.target_resource == incident_number for log in logs)

    assign_log = next(log for log in logs if log.action == "INCIDENT_ASSIGNED_TO_AMB-17")
    assert assign_log.reason == "Nearest available unit"
