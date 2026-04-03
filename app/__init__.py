from dotenv import load_dotenv
from flask import Flask, jsonify

from app.database import init_db
from app.logging_config import setup_logging
from app.metrics import metrics_bp, track_request
from app.routes import register_routes


def create_app():
    load_dotenv()

    app = Flask(__name__)

    setup_logging(app)
    init_db(app)

    from app import models  # noqa: F401 - registers models with Peewee

    register_routes(app)
    app.register_blueprint(metrics_bp)
    track_request(app)

    @app.route("/health")
    def health():
        return jsonify(status="ok")

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Internal server error"}), 500

    return app
