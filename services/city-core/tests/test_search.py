from .helpers import auth_headers

SEARCH = ["search.read"]


def test_search_requires_authentication(client) -> None:
    response = client.get("/api/v1/search", params={"q": "test"})
    assert response.status_code == 401


def test_search_rejects_wrong_permission(client) -> None:
    response = client.get(
        "/api/v1/search", headers=auth_headers(["something.unrelated"]), params={"q": "test"}
    )
    assert response.status_code == 403


def test_search_finds_road_by_name(client) -> None:
    client.post(
        "/api/v1/roads",
        headers=auth_headers(["road.create"]),
        json={"code": "ROAD-900", "name": "Harbor Expressway", "capacity": 500},
    )
    response = client.get("/api/v1/search", headers=auth_headers(SEARCH), params={"q": "harbor"})
    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "harbor"
    assert any(r["code"] == "ROAD-900" for r in body["results"]["roads"])


def test_search_finds_vehicle_by_id(client) -> None:
    client.post(
        "/api/v1/vehicles",
        headers=auth_headers(["vehicle.create"]),
        json={"vehicle_id": "BUS-9042", "vehicle_type": "public_transport"},
    )
    response = client.get("/api/v1/search", headers=auth_headers(SEARCH), params={"q": "BUS-9042"})
    vehicles = response.json()["results"]["vehicles"]
    assert any(v["vehicle_id"] == "BUS-9042" for v in vehicles)


def test_search_finds_workflow_task_by_title(client) -> None:
    client.post(
        "/api/v1/workflows",
        headers=auth_headers(["workflow.create"]),
        json={"title": "Inspect valve leak at Central Market", "department_code": "WATER"},
    )
    response = client.get(
        "/api/v1/search", headers=auth_headers(SEARCH), params={"q": "valve leak"}
    )
    tasks = response.json()["results"]["workflow_tasks"]
    assert any("valve leak" in t["title"].lower() for t in tasks)


def test_search_finds_infrastructure_asset_by_name(client) -> None:
    client.post(
        "/api/v1/infrastructure",
        headers=auth_headers(["infrastructure.create"]),
        json={
            "asset_code": "INF-BR-04",
            "name": "Harbor Suspension Bridge",
            "asset_type": "Bridge",
        },
    )
    response = client.get(
        "/api/v1/search", headers=auth_headers(SEARCH), params={"q": "suspension"}
    )
    assets = response.json()["results"]["infrastructure_assets"]
    assert any(a["asset_code"] == "INF-BR-04" for a in assets)


def test_search_respects_limit_param(client) -> None:
    for i in range(8):
        client.post(
            "/api/v1/roads",
            headers=auth_headers(["road.create"]),
            json={"code": f"ROAD-{900 + i}", "name": "Matchable Road", "capacity": 100},
        )
    response = client.get(
        "/api/v1/search", headers=auth_headers(SEARCH), params={"q": "matchable", "limit": 3}
    )
    assert len(response.json()["results"]["roads"]) == 3


def test_search_returns_empty_categories_for_no_match(client) -> None:
    response = client.get(
        "/api/v1/search", headers=auth_headers(SEARCH), params={"q": "nonexistent-xyz"}
    )
    results = response.json()["results"]
    assert all(results[key] == [] for key in results)
