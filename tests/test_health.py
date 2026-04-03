def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_404_returns_json(client):
    resp = client.get("/nonexistent-route-xyz")
    assert resp.status_code == 404
    assert "error" in resp.get_json()


def test_405_returns_json(client):
    resp = client.delete("/health")
    assert resp.status_code == 405
    assert resp.get_json()["error"] == "Method not allowed"
