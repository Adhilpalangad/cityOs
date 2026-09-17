from .helpers import auth_headers

ALL = ["incident.read", "incident.create", "incident.update", "incident.assign", "incident.resolve"]
# Matches the spec section 9 worked example for TRAFFIC_OFFICER exactly.
OFFICER = ["traffic.read", "traffic.update", "incident.create", "incident.read", "vehicle.read"]


def _create_incident(client) -> dict:
    response = client.post(
        "/api/v1/incidents",
        headers=auth_headers(ALL),
        json={
            "incident_type": "ROAD_ACCIDENT",
            "severity": "CRITICAL",
            "description": "Multi-vehicle collision",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_traffic_officer_can_create_and_read_but_not_update(client) -> None:
    created = client.post(
        "/api/v1/incidents",
        headers=auth_headers(OFFICER),
        json={"incident_type": "ROAD_ACCIDENT", "severity": "HIGH"},
    )
    assert created.status_code == 201

    forbidden = client.patch(
        f"/api/v1/incidents/{created.json()['id']}/status",
        headers=auth_headers(OFFICER),
        json={"status": "VERIFIED"},
    )
    assert forbidden.status_code == 403


def test_incident_full_lifecycle(client) -> None:
    incident = _create_incident(client)
    assert incident["status"] == "DETECTED"
    assert incident["incident_number"].startswith("INC-")

    verified = client.patch(
        f"/api/v1/incidents/{incident['id']}/status",
        headers=auth_headers(ALL),
        json={"status": "VERIFIED"},
    )
    assert verified.status_code == 200
    assert verified.json()["status"] == "VERIFIED"

    assigned = client.post(
        f"/api/v1/incidents/{incident['id']}/assign",
        headers=auth_headers(ALL),
        json={"assigned_to": "AMB-17"},
    )
    assert assigned.status_code == 200
    assert assigned.json()["status"] == "ASSIGNED"
    assert assigned.json()["assigned_to"] == "AMB-17"

    responding = client.patch(
        f"/api/v1/incidents/{incident['id']}/status",
        headers=auth_headers(ALL),
        json={"status": "RESPONDING"},
    )
    assert responding.status_code == 200

    resolved = client.post(f"/api/v1/incidents/{incident['id']}/resolve", headers=auth_headers(ALL))
    assert resolved.status_code == 200
    body = resolved.json()
    assert body["status"] == "RESOLVED"
    assert body["resolved_at"] is not None
    assert body["response_time_seconds"] >= 0

    analyzed = client.patch(
        f"/api/v1/incidents/{incident['id']}/status",
        headers=auth_headers(ALL),
        json={"status": "ANALYZED"},
    )
    assert analyzed.status_code == 200
    assert analyzed.json()["status"] == "ANALYZED"


def test_incident_cannot_skip_lifecycle_stages(client) -> None:
    incident = _create_incident(client)
    response = client.patch(
        f"/api/v1/incidents/{incident['id']}/status",
        headers=auth_headers(ALL),
        json={"status": "ASSIGNED"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INVALID_STATUS_TRANSITION"


def test_incident_cannot_assign_before_verified(client) -> None:
    incident = _create_incident(client)
    response = client.post(
        f"/api/v1/incidents/{incident['id']}/assign",
        headers=auth_headers(ALL),
        json={"assigned_to": "X"},
    )
    assert response.status_code == 409


def test_incident_cannot_resolve_before_responding(client) -> None:
    incident = _create_incident(client)
    response = client.post(f"/api/v1/incidents/{incident['id']}/resolve", headers=auth_headers(ALL))
    assert response.status_code == 409


def test_incident_has_no_delete_endpoint(client) -> None:
    incident = _create_incident(client)
    response = client.delete(f"/api/v1/incidents/{incident['id']}", headers=auth_headers(ALL))
    assert response.status_code == 405
