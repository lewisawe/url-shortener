from flask import Blueprint, jsonify, request
from playhouse.shortcuts import model_to_dict

from app.cache import cache_get, cache_set
from app.models.user import User

users_bp = Blueprint("users", __name__)


@users_bp.route("/users")
def list_users():
    page = max(1, request.args.get("page", 1, type=int))
    per_page = min(100, max(1, request.args.get("per_page", 20, type=int)))

    key = f"users:list:{page}:{per_page}"
    cached = cache_get(key)
    if cached:
        return jsonify(cached)

    users = User.select().order_by(User.id).paginate(page, per_page)
    data = [model_to_dict(u) for u in users]
    cache_set(key, data)
    return jsonify(data)


@users_bp.route("/users/<int:user_id>")
def get_user(user_id):
    key = f"users:{user_id}"
    cached = cache_get(key)
    if cached:
        return jsonify(cached)

    user = User.get_or_none(User.id == user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = model_to_dict(user)
    cache_set(key, data)
    return jsonify(data)
