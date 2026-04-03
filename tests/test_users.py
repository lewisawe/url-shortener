from app.models.user import User


def test_list_users(client, sample_user):
    resp = client.get("/users")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 1
    assert data[0]["username"] == "testuser"


def test_get_user(client, sample_user):
    resp = client.get("/users/1")
    assert resp.status_code == 200
    assert resp.get_json()["email"] == "test@example.com"


def test_get_user_not_found(client):
    resp = client.get("/users/999")
    assert resp.status_code == 404
