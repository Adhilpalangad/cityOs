from .helpers import auth_headers

ALL = ["vehicle.read", "vehicle.create", "vehicle.update", "vehicle.delete"]


def test_vehicle_lifecycle_and_position_updates(client) -> None:
    create = client.post(
        "/api/v1/vehicles",
        headers=auth_headers(ALL),
        json={"vehicle_id": "BUS_102", "vehicle_type": "public_transport"},
    )
    assert create.status_code == 201
    body = create.json()
    assert body["status"] == "ACTIVE"
    assert body["latitude"] is None
    vehicle_id = body["id"]

    position = client.put(
        f"/api/v1/vehicles/{vehicle_id}/position",
        headers=auth_headers(ALL),
        json={"latitude": 9.9816, "longitude": 76.2999, "speed_kmh": 34, "heading_degrees": 142},
    )
    assert position.status_code == 200
    body = position.json()
    assert body["latitude"] == 9.9816
    assert body["position_updated_at"] is not None

    status_update = client.patch(
        f"/api/v1/vehicles/{vehicle_id}", headers=auth_headers(ALL), json={"status": "MAINTENANCE"}
    )
    assert status_update.status_code == 200
    assert status_update.json()["status"] == "MAINTENANCE"


def test_vehicle_create_rejects_unknown_type(client) -> None:
    response = client.post(
        "/api/v1/vehicles",
        headers=auth_headers(ALL),
        json={"vehicle_id": "X1", "vehicle_type": "spaceship"},
    )
    assert response.status_code == 422


def test_vehicle_create_rejects_duplicate_id(client) -> None:
    payload = {"vehicle_id": "BUS_1", "vehicle_type": "fleet"}
    first = client.post("/api/v1/vehicles", headers=auth_headers(ALL), json=payload)
    assert first.status_code == 201
    second = client.post("/api/v1/vehicles", headers=auth_headers(ALL), json=payload)
    assert second.status_code == 409
