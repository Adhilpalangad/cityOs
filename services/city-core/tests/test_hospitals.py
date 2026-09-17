from .helpers import auth_headers

ALL = ["hospital.read", "hospital.create", "hospital.update", "hospital.delete"]


def _create_hospital(client) -> str:
    response = client.post(
        "/api/v1/hospitals",
        headers=auth_headers(ALL),
        json={
            "code": "H-12",
            "name": "City General",
            "latitude": 9.98,
            "longitude": 76.28,
            "beds_total": 420,
            "icu_total": 50,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_hospital_crud_lifecycle(client) -> None:
    hospital_id = _create_hospital(client)

    updated = client.patch(
        f"/api/v1/hospitals/{hospital_id}",
        headers=auth_headers(ALL),
        json={"beds_occupied": 386, "icu_occupied": 42, "emergency_capacity": "HIGH"},
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["beds_occupied"] == 386
    assert body["emergency_capacity"] == "HIGH"

    deleted = client.delete(f"/api/v1/hospitals/{hospital_id}", headers=auth_headers(ALL))
    assert deleted.status_code == 204


def test_hospital_rejects_occupancy_over_capacity(client) -> None:
    hospital_id = _create_hospital(client)
    response = client.patch(
        f"/api/v1/hospitals/{hospital_id}", headers=auth_headers(ALL), json={"beds_occupied": 999}
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_CAPACITY"


def test_hospital_create_rejects_negative_capacity(client) -> None:
    response = client.post(
        "/api/v1/hospitals",
        headers=auth_headers(ALL),
        json={
            "code": "H-99",
            "name": "Bad Hospital",
            "latitude": 0,
            "longitude": 0,
            "beds_total": -1,
        },
    )
    assert response.status_code == 422
