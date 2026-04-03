from app.models.url import Url
from app.models.user import User


def test_list_urls(client, sample_url):
    resp = client.get("/urls")
    assert resp.status_code == 200
    assert len(resp.get_json()) == 1


def test_get_url(client, sample_url):
    resp = client.get("/urls/1")
    assert resp.status_code == 200
    assert resp.get_json()["short_code"] == "abc123"


def test_get_url_not_found(client):
    resp = client.get("/urls/999")
    assert resp.status_code == 404


def test_create_url(client, sample_user):
    resp = client.post("/urls", json={
        "user_id": sample_user.id,
        "original_url": "https://example.com/new",
        "title": "New Link",
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["original_url"] == "https://example.com/new"
    assert len(data["short_code"]) == 6


def test_create_url_missing_fields(client):
    resp = client.post("/urls", json={"title": "no url"})
    assert resp.status_code == 400


def test_create_url_invalid_url(client, sample_user):
    resp = client.post("/urls", json={
        "user_id": sample_user.id,
        "original_url": "not-a-url",
    })
    assert resp.status_code == 400
    assert "Invalid URL" in resp.get_json()["error"]


def test_create_url_nonexistent_user(client):
    resp = client.post("/urls", json={
        "user_id": 9999,
        "original_url": "https://example.com",
    })
    assert resp.status_code == 404


def test_create_url_no_body(client):
    resp = client.post("/urls", content_type="application/json")
    assert resp.status_code == 400


def test_update_url(client, sample_url):
    resp = client.put("/urls/1", json={"title": "Updated"})
    assert resp.status_code == 200
    assert resp.get_json()["title"] == "Updated"


def test_update_url_invalid_url(client, sample_url):
    resp = client.put("/urls/1", json={"original_url": "bad"})
    assert resp.status_code == 400


def test_update_url_not_found(client):
    resp = client.put("/urls/999", json={"title": "x"})
    assert resp.status_code == 404


def test_delete_url(client, sample_url):
    resp = client.delete("/urls/1")
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "URL deleted"


def test_delete_url_not_found(client):
    resp = client.delete("/urls/999")
    assert resp.status_code == 404


def test_redirect_short_code(client, sample_url):
    resp = client.get("/abc123")
    assert resp.status_code == 302
    assert "example.com" in resp.headers["Location"]


def test_redirect_inactive(client, sample_url):
    sample_url.is_active = False
    sample_url.save()
    resp = client.get("/abc123")
    assert resp.status_code == 410


def test_redirect_not_found(client):
    resp = client.get("/nope99")
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "Short code not found"


def test_pagination_bounds(client, sample_url):
    resp = client.get("/urls?page=-1&per_page=0")
    assert resp.status_code == 200


def test_pagination_non_integer(client):
    resp = client.get("/urls?page=abc")
    assert resp.status_code == 200
