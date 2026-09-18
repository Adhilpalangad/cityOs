"""Notification Engine tests: the CRUD surface (routes_notifications.py)
and all three trigger rules from app/services/notifications.py, wired into
incidents, roads, and hospitals respectively.
"""

from .helpers import auth_headers

NOTIF_PERMS = ["notification.read", "notification.create"]
INCIDENT_PERMS = ["incident.read", "incident.create"]
ROAD_PERMS = ["road.read", "road.create", "road.update"]
HOSPITAL_PERMS = ["hospital.read", "hospital.create", "hospital.update"]


def test_create_notification_manually(client) -> None:
    response = client.post(
        "/api/v1/notifications",
        headers=auth_headers(NOTIF_PERMS),
        json={"title": "Maintenance window", "message": "Scheduled 2am-4am.", "severity": "INFO"},
    )
    assert response.status_code == 201
    assert response.json()["is_read"] is False


def test_create_notification_rejects_unknown_severity(client) -> None:
    response = client.post(
        "/api/v1/notifications",
        headers=auth_headers(NOTIF_PERMS),
        json={"title": "X", "message": "Y", "severity": "URGENT"},
    )
    assert response.status_code == 422


def test_mark_notification_read(client) -> None:
    created = client.post(
        "/api/v1/notifications",
        headers=auth_headers(NOTIF_PERMS),
        json={"title": "X", "message": "Y"},
    )
    notification_id = created.json()["id"]

    marked = client.patch(
        f"/api/v1/notifications/{notification_id}/read", headers=auth_headers(NOTIF_PERMS)
    )
    assert marked.status_code == 200
    assert marked.json()["is_read"] is True


def test_list_notifications_filters_by_read_status(client) -> None:
    created = client.post(
        "/api/v1/notifications",
        headers=auth_headers(NOTIF_PERMS),
        json={"title": "X", "message": "Y"},
    )
    client.patch(
        f"/api/v1/notifications/{created.json()['id']}/read", headers=auth_headers(NOTIF_PERMS)
    )
    client.post(
        "/api/v1/notifications",
        headers=auth_headers(NOTIF_PERMS),
        json={"title": "Z", "message": "W"},
    )

    unread = client.get(
        "/api/v1/notifications", headers=auth_headers(NOTIF_PERMS), params={"is_read": False}
    )
    assert unread.json()["meta"]["total"] == 1


def test_critical_incident_triggers_notification(client) -> None:
    client.post(
        "/api/v1/incidents",
        headers=auth_headers(INCIDENT_PERMS),
        json={"incident_type": "FIRE", "severity": "CRITICAL", "department_code": "EMERGENCY"},
    )

    notifs = client.get("/api/v1/notifications", headers=auth_headers(NOTIF_PERMS))
    items = notifs.json()["items"]
    assert any(n["severity"] == "CRITICAL" and n["target_department"] == "EMERGENCY" for n in items)


def test_non_critical_incident_does_not_trigger_notification(client) -> None:
    client.post(
        "/api/v1/incidents",
        headers=auth_headers(INCIDENT_PERMS),
        json={"incident_type": "FIRE", "severity": "LOW"},
    )
    notifs = client.get("/api/v1/notifications", headers=auth_headers(NOTIF_PERMS))
    assert notifs.json()["meta"]["total"] == 0


def test_road_closure_triggers_notification(client) -> None:
    created = client.post(
        "/api/v1/roads",
        headers=auth_headers(ROAD_PERMS),
        json={"code": "ROAD-900", "name": "Test Road", "capacity": 500},
    )
    client.patch(
        f"/api/v1/roads/{created.json()['id']}",
        headers=auth_headers(ROAD_PERMS, department="TRAFFIC"),
        json={"status": "CLOSED", "reason": "Water main repair"},
    )

    notifs = client.get("/api/v1/notifications", headers=auth_headers(NOTIF_PERMS))
    items = notifs.json()["items"]
    assert any("ROAD-900" in n["message"] or "Test Road" in n["title"] for n in items)


def test_hospital_icu_threshold_triggers_notification_once(client) -> None:
    created = client.post(
        "/api/v1/hospitals",
        headers=auth_headers(HOSPITAL_PERMS),
        json={
            "code": "H-12",
            "name": "City General",
            "latitude": 9.98,
            "longitude": 76.28,
            "beds_total": 100,
            "icu_total": 10,
        },
    )
    hospital_id = created.json()["id"]

    # Crosses the 90% threshold (9/10).
    client.patch(
        f"/api/v1/hospitals/{hospital_id}",
        headers=auth_headers(HOSPITAL_PERMS),
        json={"icu_occupied": 9},
    )
    # Stays over threshold -- should not fire a second notification.
    client.patch(
        f"/api/v1/hospitals/{hospital_id}",
        headers=auth_headers(HOSPITAL_PERMS),
        json={"icu_occupied": 10},
    )

    notifs = client.get("/api/v1/notifications", headers=auth_headers(NOTIF_PERMS))
    items = notifs.json()["items"]
    icu_alerts = [n for n in items if n["target_department"] == "HEALTHCARE"]
    assert len(icu_alerts) == 1
    assert icu_alerts[0]["severity"] == "CRITICAL"


def test_hospital_below_threshold_does_not_trigger_notification(client) -> None:
    created = client.post(
        "/api/v1/hospitals",
        headers=auth_headers(HOSPITAL_PERMS),
        json={
            "code": "H-13",
            "name": "Metro Medical",
            "latitude": 9.98,
            "longitude": 76.28,
            "beds_total": 100,
            "icu_total": 10,
        },
    )
    client.patch(
        f"/api/v1/hospitals/{created.json()['id']}",
        headers=auth_headers(HOSPITAL_PERMS),
        json={"icu_occupied": 5},
    )
    notifs = client.get("/api/v1/notifications", headers=auth_headers(NOTIF_PERMS))
    assert notifs.json()["meta"]["total"] == 0
