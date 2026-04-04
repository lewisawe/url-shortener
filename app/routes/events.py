from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from playhouse.shortcuts import model_to_dict

from app.cache import cache_delete_pattern, cache_get, cache_set
from app.models.event import Event
from app.models.url import Url
from app.models.user import User

events_bp = Blueprint("events", __name__)


@events_bp.route("/events")
def list_events():
    page = max(1, request.args.get("page", 1, type=int))
    per_page = min(100, max(1, request.args.get("per_page", 20, type=int)))

    key = f"events:list:{page}:{per_page}"
    cached = cache_get(key)
    if cached:
        return jsonify(cached)

    events = Event.select().order_by(Event.id).paginate(page, per_page)
    data = [model_to_dict(e) for e in events]
    cache_set(key, data, ttl=30)
    return jsonify(data)


@events_bp.route("/events", methods=["POST"])
def create_event():
    data = request.get_json(silent=True)
    if not data or "event_type" not in data or "url_id" not in data or "user_id" not in data:
        return jsonify({"error": "event_type, url_id, and user_id are required"}), 400

    url = Url.get_or_none(Url.id == data["url_id"])
    if not url:
        return jsonify({"error": "URL not found"}), 404

    user = User.get_or_none(User.id == data["user_id"])
    if not user:
        return jsonify({"error": "User not found"}), 404

    details = data.get("details")
    if isinstance(details, dict):
        import json
        details = json.dumps(details)

    event = Event.create(
        url=url,
        user=user,
        event_type=data["event_type"],
        timestamp=datetime.now(timezone.utc),
        details=details,
    )
    cache_delete_pattern("events:list:*")
    return jsonify(model_to_dict(event)), 201
