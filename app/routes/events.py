from flask import Blueprint, jsonify, request
from playhouse.shortcuts import model_to_dict

from app.models.event import Event

events_bp = Blueprint("events", __name__)


@events_bp.route("/events")
def list_events():
    page = max(1, request.args.get("page", 1, type=int))
    per_page = min(100, max(1, request.args.get("per_page", 20, type=int)))
    events = Event.select().order_by(Event.id).paginate(page, per_page)
    return jsonify([model_to_dict(e) for e in events])
