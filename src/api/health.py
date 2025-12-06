from datetime import datetime, timezone
from flask_smorest import Blueprint
from flask import jsonify

blp = Blueprint(
    "Health",
    __name__,
    url_prefix="/health",
    description="Health check endpoint",
)

@blp.route("", methods=["GET"])
def health_check():
    return jsonify(
        {
            "status": "OK",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "bookstore-backend",
            "version": "1.0.0",
        }
    )
