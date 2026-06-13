import time
from datetime import datetime, timezone

import flask
from flask import Blueprint, jsonify

from app.database import db

health_bp = Blueprint("health", __name__)
_START_TIME = time.monotonic()


@health_bp.get("/health")
def health():
    """
    Santé de l'application
    ---
    tags:
      - Santé
    responses:
      200:
        description: Application opérationnelle
        schema:
          properties:
            status:        {type: string, example: ok}
            service:       {type: string}
            version:       {type: string}
            environment:   {type: string}
            uptime_seconds:{type: number}
            timestamp:     {type: string, format: date-time}
            dependencies:
              type: object
              properties:
                database:  {type: string, example: ok}
      503:
        description: Base de données inaccessible
    """
    try:
        db.session.execute(db.text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"

    ok = db_status == "ok"
    return jsonify({
        "status": "ok" if ok else "degraded",
        "service": flask.current_app.config["SERVICE_NAME"],
        "version": flask.current_app.config["SERVICE_VERSION"],
        "environment": flask.current_app.config["DEPLOYMENT_ENVIRONMENT"],
        "uptime_seconds": round(time.monotonic() - _START_TIME, 1),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dependencies": {"database": db_status},
    }), 200 if ok else 503
