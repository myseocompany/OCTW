from __future__ import annotations

from fastapi.testclient import TestClient

from octw.edge.proxy import edge_app


def test_edge_health_route_is_not_captured_by_slug_route():
    client = TestClient(edge_app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "octw-edge"}
