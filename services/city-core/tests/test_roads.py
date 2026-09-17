from .helpers import auth_headers

READ = ["road.read"]
ALL = ["road.read", "road.create", "road.update", "road.delete"]


def test_list_roads_requires_permission(client) -> None:
    response = client.get("/api/v1/roads")
    assert response.status_code == 401

    response = client.get("/api/v1/roads", headers=auth_headers([]))
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"


def test_road_crud_lifecycle(client) -> None:
    create = client.post(
        "/api/v1/roads",
        headers=auth_headers(ALL),
        json={
            "code": "ROAD_1024",
            "name": "MG Road",
            "capacity": 900,
            "waypoints": [[9.98, 76.28]],
        },
    )
    assert create.status_code == 201
    body = create.json()
    assert body["status"] == "OPEN"
    assert body["traffic_level"] == "LOW"
    road_id = body["id"]

    duplicate = client.post(
        "/api/v1/roads", headers=auth_headers(ALL), json={"code": "ROAD_1024", "name": "Dup"}
    )
    assert duplicate.status_code == 409

    updated = client.patch(
        f"/api/v1/roads/{road_id}",
        headers=auth_headers(ALL),
        json={"traffic_level": "HIGH", "risk_level": "HIGH", "current_vehicle_count": 843},
    )
    assert updated.status_code == 200
    assert updated.json()["traffic_level"] == "HIGH"
    assert updated.json()["current_vehicle_count"] == 843

    fetched = client.get(f"/api/v1/roads/{road_id}", headers=auth_headers(READ))
    assert fetched.status_code == 200
    assert fetched.json()["risk_level"] == "HIGH"

    deleted = client.delete(f"/api/v1/roads/{road_id}", headers=auth_headers(ALL))
    assert deleted.status_code == 204

    missing = client.get(f"/api/v1/roads/{road_id}", headers=auth_headers(READ))
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "ROAD_NOT_FOUND"


def test_road_update_rejects_invalid_status(client) -> None:
    create = client.post(
        "/api/v1/roads", headers=auth_headers(ALL), json={"code": "ROAD_2000", "name": "Ring Road"}
    )
    road_id = create.json()["id"]
    response = client.patch(
        f"/api/v1/roads/{road_id}", headers=auth_headers(ALL), json={"status": "ON_FIRE"}
    )
    assert response.status_code == 422


def test_road_search_and_pagination(client) -> None:
    for i in range(3):
        client.post(
            "/api/v1/roads",
            headers=auth_headers(ALL),
            json={"code": f"RD_{i}", "name": f"Road {i}"},
        )

    paged = client.get("/api/v1/roads?page=1&page_size=2", headers=auth_headers(READ))
    assert paged.status_code == 200
    body = paged.json()
    assert len(body["items"]) == 2
    assert body["meta"]["total"] == 3
    assert body["meta"]["total_pages"] == 2

    searched = client.get("/api/v1/roads?q=RD_1", headers=auth_headers(READ))
    assert searched.status_code == 200
    assert [item["code"] for item in searched.json()["items"]] == ["RD_1"]
