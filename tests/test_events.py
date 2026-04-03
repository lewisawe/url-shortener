from app.models.event import Event


def test_list_events(client, sample_url):
    Event.create(
        url=sample_url,
        user=sample_url.user,
        event_type="created",
        timestamp="2025-01-01 00:00:00",
    )
    resp = client.get("/events")
    assert resp.status_code == 200
    assert len(resp.get_json()) == 1
