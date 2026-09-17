from sqlalchemy import select

from app.db.models import AuditLog, Notification

from .helpers import auth_headers

ALL = ["complaint.read", "complaint.create", "complaint.update"]


def _create_complaint(client, **overrides) -> dict:
    payload = {
        "title": "Pothole near Hospital Gate",
        "description": "Deep pothole causing severe traffic slowdown.",
        "reporter_email": "citizen@example.com",
    }
    payload.update(overrides)
    response = client.post("/api/v1/complaints", headers=auth_headers(ALL), json=payload)
    assert response.status_code == 201
    return response.json()


def test_create_complaint_defaults(client) -> None:
    complaint = _create_complaint(client)
    assert complaint["complaint_number"].startswith("CMP-")
    assert complaint["status"] == "SUBMITTED"
    assert complaint["department_code"] is None


def test_complaint_cannot_skip_to_resolved(client) -> None:
    complaint = _create_complaint(client)
    response = client.patch(
        f"/api/v1/complaints/{complaint['id']}/status",
        headers=auth_headers(ALL),
        json={"status": "RESOLVED"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INVALID_STATUS_TRANSITION"


async def test_full_complaint_lifecycle_writes_audit_and_notification(client, db) -> None:
    complaint = _create_complaint(client)

    reviewed = client.patch(
        f"/api/v1/complaints/{complaint['id']}/status",
        headers=auth_headers(ALL, email="officer@cityos.example"),
        json={"status": "IN_REVIEW"},
    )
    assert reviewed.status_code == 200

    assigned = client.patch(
        f"/api/v1/complaints/{complaint['id']}/status",
        headers=auth_headers(ALL, email="officer@cityos.example"),
        json={"status": "ASSIGNED", "department_code": "INFRASTRUCTURE"},
    )
    assert assigned.status_code == 200
    assert assigned.json()["department_code"] == "INFRASTRUCTURE"

    resolved = client.patch(
        f"/api/v1/complaints/{complaint['id']}/status",
        headers=auth_headers(ALL, email="officer@cityos.example"),
        json={"status": "RESOLVED", "reason": "Pothole filled and resurfaced."},
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "RESOLVED"

    logs = (await db.scalars(select(AuditLog))).all()
    actions = [log.action for log in logs]
    assert "COMPLAINT_SUBMITTED_TO_IN_REVIEW" in actions
    assert "COMPLAINT_IN_REVIEW_TO_ASSIGNED" in actions
    assert "COMPLAINT_ASSIGNED_TO_RESOLVED" in actions

    notifications = (await db.scalars(select(Notification))).all()
    assert len(notifications) == 1
    assert notifications[0].channel == "EMAIL"
    assert "resolved" in notifications[0].title.lower()


async def test_rejected_complaint_does_not_send_resolution_notification(client, db) -> None:
    complaint = _create_complaint(client)
    client.patch(
        f"/api/v1/complaints/{complaint['id']}/status",
        headers=auth_headers(ALL),
        json={"status": "IN_REVIEW"},
    )
    rejected = client.patch(
        f"/api/v1/complaints/{complaint['id']}/status",
        headers=auth_headers(ALL),
        json={"status": "REJECTED", "reason": "Duplicate of CMP-existing"},
    )
    assert rejected.status_code == 200

    notifications = (await db.scalars(select(Notification))).all()
    assert notifications == []


def test_complaint_has_no_delete_endpoint(client) -> None:
    complaint = _create_complaint(client)
    response = client.delete(f"/api/v1/complaints/{complaint['id']}", headers=auth_headers(ALL))
    assert response.status_code == 405
