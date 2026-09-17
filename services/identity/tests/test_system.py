def test_root(client) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"name": "CityOS Identity Service", "status": "online"}


def test_health(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "identity"}
    assert response.headers["X-Request-ID"].startswith("req_")
