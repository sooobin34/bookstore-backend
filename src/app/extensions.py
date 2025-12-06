from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_smorest import Api
from flask_cors import CORS

from src.app.common.errors import error_response


db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
api = Api()
cors = CORS()

# 간단한 전역 레이트 리밋 설정
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute"],
)

# JWT: Authorization 헤더 없음(401)일 때 우리 공통 에러 포맷으로 응답
@jwt.unauthorized_loader
def handle_missing_authorization(err):
    return error_response(
        status=401,
        code="UNAUTHORIZED",
        message="Missing Authorization Header",
    ), 401