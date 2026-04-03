import json
import logging
import sys
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        })


def setup_logging(app):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    app.logger.handlers = [handler]
    app.logger.setLevel(logging.INFO)

    logging.getLogger("werkzeug").handlers = [handler]
    logging.getLogger("werkzeug").setLevel(logging.INFO)
