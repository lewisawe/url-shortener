import os
import resource
import time

from flask import Blueprint, jsonify, request

metrics_bp = Blueprint("metrics", __name__)

REQUEST_COUNT = {}
ERROR_COUNT = {}
START_TIME = time.time()


def track_request(app):
    @app.before_request
    def _before():
        request._start_time = time.time()

    @app.after_request
    def _after(response):
        endpoint = request.endpoint or "unknown"
        REQUEST_COUNT[endpoint] = REQUEST_COUNT.get(endpoint, 0) + 1
        if response.status_code >= 400:
            ERROR_COUNT[endpoint] = ERROR_COUNT.get(endpoint, 0) + 1
        return response


@metrics_bp.route("/metrics")
def metrics():
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return jsonify({
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "total_requests": sum(REQUEST_COUNT.values()),
        "total_errors": sum(ERROR_COUNT.values()),
        "requests_by_endpoint": REQUEST_COUNT,
        "errors_by_endpoint": ERROR_COUNT,
        "memory_mb": round(usage.ru_maxrss / 1024, 1),
        "cpu_user_seconds": round(usage.ru_utime, 2),
        "cpu_system_seconds": round(usage.ru_stime, 2),
        "pid": os.getpid(),
    })
