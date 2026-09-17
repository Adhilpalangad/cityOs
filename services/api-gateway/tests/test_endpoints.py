from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"name": "CityOS API Gateway", "status": "online"}


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "api-gateway"}
    assert response.headers["X-Request-ID"].startswith("req_")


def test_system_info() -> None:
    response = client.get("/api/v1/system/info")
    assert response.status_code == 200
    assert response.json()["name"] == "CityOS"
    assert response.json()["version"] == "0.1.0"
