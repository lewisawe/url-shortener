from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from playhouse.shortcuts import model_to_dict

from app.cache import cache_delete_pattern, cache_get, cache_set
from app.database import db
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


@users_bp.route("/users", methods=["POST"])
def create_user():
    data = request.get_json(silent=True)
    if not data or "username" not in data or "email" not in data:
        return jsonify({"error": "username and email are required"}), 400

    if User.get_or_none(User.username == data["username"]):
        return jsonify({"error": "Username already exists"}), 400
    if User.get_or_none(User.email == data["email"]):
        return jsonify({"error": "Email already exists"}), 400

    user = User.create(
        username=data["username"],
        email=data["email"],
        created_at=datetime.now(timezone.utc),
    )
    cache_delete_pattern("users:list:*")
    return jsonify(model_to_dict(user)), 201


@users_bp.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    user = User.get_or_none(User.id == user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No data provided"}), 400

    if "username" in data:
        user.username = data["username"]
    if "email" in data:
        user.email = data["email"]
    user.save()

    cache_delete_pattern(f"users:{user_id}")
    cache_delete_pattern("users:list:*")
    return jsonify(model_to_dict(user))


@users_bp.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    user = User.get_or_none(User.id == user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.delete_instance(recursive=True)
    cache_delete_pattern(f"users:{user_id}")
    cache_delete_pattern("users:list:*")
    return jsonify({"message": "User deleted"}), 200
