import httpx
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_proxy_forwards_method_path_and_query_to_identity_service(monkeypatch) -> None:
    captured = {}

    async def fake_request(self, method, url, params=None, headers=None, content=None):
        captured.update(method=method, url=url, params=params)
        return httpx.Response(200, json={"ok": True}, headers={"X-Upstream": "identity"})

    monkeypatch.setattr(httpx.AsyncClient, "request", fake_request)

    response = client.get("/api/v1/users?page=2")

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert response.headers.get("x-upstream") == "identity"
    assert captured["method"] == "GET"
    assert captured["url"].endswith("/api/v1/users")
    assert captured["params"] == "page=2"


def test_proxy_forwards_nested_paths(monkeypatch) -> None:
    async def fake_request(self, method, url, params=None, headers=None, content=None):
        assert url.endswith("/api/v1/auth/login")
        return httpx.Response(200, json={"ok": True})

    monkeypatch.setattr(httpx.AsyncClient, "request", fake_request)

    response = client.post("/api/v1/auth/login", json={"email": "a@b.com", "password": "x"})
    assert response.status_code == 200


def test_proxy_relays_redirects_without_following_them(monkeypatch) -> None:
    async def fake_request(self, method, url, params=None, headers=None, content=None):
        assert url.endswith("/api/v1/auth/oauth/google/authorize")
        return httpx.Response(
            302, headers={"Location": "https://accounts.google.com/o/oauth2/v2/auth"}
        )

    monkeypatch.setattr(httpx.AsyncClient, "request", fake_request)

    response = client.get("/api/v1/auth/oauth/google/authorize", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "https://accounts.google.com/o/oauth2/v2/auth"


def test_proxy_routes_city_core_prefixes_to_the_city_core_service(monkeypatch) -> None:
    from app.core.config import get_settings

    captured = {}

    async def fake_request(self, method, url, params=None, headers=None, content=None):
        captured["url"] = url
        return httpx.Response(200, json={"ok": True})

    monkeypatch.setattr(httpx.AsyncClient, "request", fake_request)

    response = client.get("/api/v1/roads/123")
    assert response.status_code == 200
    assert captured["url"] == f"{get_settings().city_core_service_url}/api/v1/roads/123"


def test_non_proxied_routes_are_unaffected() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "api-gateway"
