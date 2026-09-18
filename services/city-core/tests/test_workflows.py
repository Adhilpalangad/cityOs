from sqlalchemy import select

from app.db.models import AuditLog

from .helpers import auth_headers

ALL = ["workflow.read", "workflow.create", "workflow.update", "workflow.assign"]


def _create_task(client, **overrides) -> dict:
    payload = {"title": "Inspect valve leak at Central Market", "department_code": "WATER"}
    payload.update(overrides)
    response = client.post("/api/v1/workflows", headers=auth_headers(ALL), json=payload)
    assert response.status_code == 201
    return response.json()


def test_create_workflow_task_defaults(client) -> None:
    task = _create_task(client)
    assert task["task_number"].startswith("TSK-")
    assert task["status"] == "PENDING"
    assert task["priority"] == "MEDIUM"
    assert task["assigned_to"] is None


def test_create_workflow_task_rejects_unknown_priority(client) -> None:
    response = client.post(
        "/api/v1/workflows",
        headers=auth_headers(ALL),
        json={"title": "X", "department_code": "WATER", "priority": "URGENT"},
    )
    assert response.status_code == 422


def test_workflow_task_list_and_filter(client) -> None:
    _create_task(client, department_code="WATER")
    _create_task(client, department_code="ENERGY")

    all_tasks = client.get("/api/v1/workflows", headers=auth_headers(ALL))
    assert all_tasks.json()["meta"]["total"] == 2

    water_only = client.get(
        "/api/v1/workflows", headers=auth_headers(ALL), params={"department_code": "WATER"}
    )
    assert water_only.json()["meta"]["total"] == 1


async def test_assign_and_status_transitions_write_audit_entries(client, db) -> None:
    task = _create_task(client)
    client.post(
        f"/api/v1/workflows/{task['id']}/assign",
        headers=auth_headers(ALL, email="dispatcher@cityos.example", department="WATER"),
        json={"assigned_to": "Engineer R. Sharma", "reason": "Nearest on-call engineer"},
    )

    in_progress = client.patch(
        f"/api/v1/workflows/{task['id']}/status",
        headers=auth_headers(ALL),
        json={"status": "IN_PROGRESS"},
    )
    assert in_progress.status_code == 200

    completed = client.patch(
        f"/api/v1/workflows/{task['id']}/status",
        headers=auth_headers(ALL),
        json={"status": "COMPLETED", "reason": "Valve replaced"},
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "COMPLETED"

    logs = (await db.scalars(select(AuditLog).order_by(AuditLog.timestamp))).all()
    actions = [log.action for log in logs]
    assert "WORKFLOW_TASK_ASSIGNED_TO_Engineer R. Sharma" in actions
    assert "WORKFLOW_TASK_PENDING_TO_IN_PROGRESS" in actions
    assert "WORKFLOW_TASK_IN_PROGRESS_TO_COMPLETED" in actions


def test_workflow_task_cannot_skip_to_completed(client) -> None:
    task = _create_task(client)
    response = client.patch(
        f"/api/v1/workflows/{task['id']}/status",
        headers=auth_headers(ALL),
        json={"status": "COMPLETED"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INVALID_STATUS_TRANSITION"


def test_workflow_task_terminal_states_have_no_further_transitions(client) -> None:
    task = _create_task(client)
    client.patch(
        f"/api/v1/workflows/{task['id']}/status",
        headers=auth_headers(ALL),
        json={"status": "REJECTED"},
    )
    response = client.patch(
        f"/api/v1/workflows/{task['id']}/status",
        headers=auth_headers(ALL),
        json={"status": "IN_PROGRESS"},
    )
    assert response.status_code == 409


def test_workflow_task_has_no_delete_endpoint(client) -> None:
    task = _create_task(client)
    response = client.delete(f"/api/v1/workflows/{task['id']}", headers=auth_headers(ALL))
    assert response.status_code == 405
