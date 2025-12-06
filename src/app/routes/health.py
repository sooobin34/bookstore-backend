from datetime import datetime
from flask_smorest import Blueprint
from marshmallow import Schema, fields

class HealthSchema(Schema):
    status = fields.Str(required=True)
    version = fields.Str(required=True)
    time = fields.DateTime(required=True)

blp = Blueprint(
    "health",
    "health",
    url_prefix="/health",
    description="Health check endpoint",
)

@blp.route("")
@blp.response(200, HealthSchema)
def health():
    """
    단순 헬스체크 엔드포인트.
    인증 없이 접근 가능, 배포/헬스체크용.
    """
    return {
        "status": "UP",
        "version": "1.0.0",
        "time": datetime.utcnow(),
    }
