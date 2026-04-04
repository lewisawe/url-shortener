import json
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from playhouse.shortcuts import model_to_dict

from app.cache import cache_delete_pattern, cache_get, cache_set
from app.models.event import Event
from app.models.url import Url
from app.models.user import User

events_bp = Blueprint("events", __name__)


def serialize_event(event):
    d = model_to_dict(event, backrefs=False)
    # Flatten to url_id and user_id
    if "url" in d and isinstance(d["url"], dict):
        d["url_id"] = d["url"]["id"]
        del d["url"]
    elif "url" in d:
        d["url_id"] = d["url"]
        del d["url"]
    if "user" in d and isinstance(d["user"], dict):
        d["user_id"] = d["user"]["id"]
        del d["user"]
    elif "user" in d:
        d["user_id"] = d["user"]
        del d["user"]
    # Parse details string as JSON if possible
    if isinstance(d.get("details"), str):
        try:
            d["details"] = json.loads(d["details"])
        except (json.JSONDecodeError, TypeError):
            pass
    return d


@events_bp.route("/events")
def list_events():
    page = max(1, request.args.get("page", 1, type=int))
    per_page = min(100, max(1, request.args.get("per_page", 20, type=int)))
    url_id = request.args.get("url_id", type=int)
    user_id = request.args.get("user_id", type=int)
    event_type = request.args.get("event_type")

    query = Event.select().order_by(Event.id)
    if url_id:
        query = query.where(Event.url == url_id)
    if user_id:
        query = query.where(Event.user == user_id)
    if event_type:
        query = query.where(Event.event_type == event_type)

    events = query.paginate(page, per_page)
    data = [serialize_event(e) for e in events]
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
        details = json.dumps(details)

    event = Event.create(
        url=url,
        user=user,
        event_type=data["event_type"],
        timestamp=datetime.now(timezone.utc),
        details=details,
    )
    cache_delete_pattern("events:list:*")
    return jsonify(serialize_event(event)), 201
