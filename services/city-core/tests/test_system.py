def test_root(client) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"name": "CityOS City Core Service", "status": "online"}


def test_health(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "city-core"}
    assert response.headers["X-Request-ID"].startswith("req_")
