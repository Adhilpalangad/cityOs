"""Confirms every endpoint that used to live in routes_extended.py with no
authentication at all now requires it, same as every other endpoint in
this service. Before this, `/api/v1/audit` -- audit logs, which spec
section 50 explicitly says should be "protected from ordinary users" --
was reachable by anyone, no token required.
"""

import pytest

from .helpers import auth_headers

GET_ENDPOINTS = [
    "/api/v1/routes",
    "/api/v1/stops",
    "/api/v1/water",
    "/api/v1/energy",
    "/api/v1/environment",
    "/api/v1/complaints",
    "/api/v1/audit",
    "/api/v1/simulations",
    "/api/v1/knowledge",
    "/api/v1/analytics",
]


@pytest.mark.parametrize("path", GET_ENDPOINTS)
def test_get_endpoint_requires_authentication(client, path) -> None:
    response = client.get(path)
    assert response.status_code == 401, f"{path} should require authentication"


@pytest.mark.parametrize(
    ("path", "permission"),
    [
        ("/api/v1/routes", "transit.read"),
        ("/api/v1/stops", "transit.read"),
        ("/api/v1/water", "water.read"),
        ("/api/v1/energy", "energy.read"),
        ("/api/v1/environment", "environment.read"),
        ("/api/v1/complaints", "complaint.read"),
        ("/api/v1/audit", "audit.read"),
        ("/api/v1/simulations", "simulation.read"),
        ("/api/v1/knowledge", "knowledge.read"),
        ("/api/v1/analytics", "analytics.read"),
    ],
)
def test_get_endpoint_rejects_wrong_permission(client, path, permission) -> None:
    response = client.get(path, headers=auth_headers(["something.unrelated"]))
    assert response.status_code == 403
    response = client.get(path, headers=auth_headers([permission]))
    assert response.status_code == 200


def test_create_complaint_requires_authentication(client) -> None:
    response = client.post("/api/v1/complaints", json={"title": "Pothole", "description": "x"})
    assert response.status_code == 401


def test_create_complaint_with_permission_succeeds(client) -> None:
    response = client.post(
        "/api/v1/complaints",
        headers=auth_headers(["complaint.create"]),
        json={"title": "Pothole on Main St", "description": "Large pothole", "category": "ROADS"},
    )
    assert response.status_code == 201


def test_create_simulation_requires_authentication(client) -> None:
    response = client.post("/api/v1/simulations", json={"name": "Test"})
    assert response.status_code == 401


def test_ai_analyze_requires_authentication(client) -> None:
    response = client.post("/api/v1/ai/analyze", json={"query": "What is happening?"})
    assert response.status_code == 401


def test_ai_analyze_with_permission_succeeds(client) -> None:
    response = client.post(
        "/api/v1/ai/analyze", headers=auth_headers(["ai.analyze"]), json={"query": "status?"}
    )
    assert response.status_code == 200
