import logging
import time

from flask import Flask, request

from .extensions import db, migrate, jwt, limiter, cors
from .config import Config
from src.api import init_app as init_api


def create_app(config_class: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Swagger / OpenAPI 설정
    app.config.update(
        API_TITLE="Bookstore API",
        API_VERSION="v1",
        OPENAPI_VERSION="3.0.3",
        # /openapi.json 이 여기서 제공됨
        OPENAPI_URL_PREFIX="/",
        # Swagger UI 접속 경로: http://127.0.0.1:5000/swagger-ui
        OPENAPI_SWAGGER_UI_PATH="/swagger-ui",
        OPENAPI_SWAGGER_UI_URL="https://cdn.jsdelivr.net/npm/swagger-ui-dist/",
    )

    # 확장 기능 초기화
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)
    cors.init_app(app, resources={r"/*": {"origins": "*"}})

    # API 블루프린트 등록 (health, books, auth, users, reviews, cart, orders)
    init_api(app)

    # 요청/응답 로깅 (1-9 항목용)
    logger = app.logger
    logger.setLevel(logging.INFO)

    @app.before_request
    def start_timer():
        request.start_time = time.time()

    @app.after_request
    def log_request(response):
        try:
            duration = time.time() - getattr(request, "start_time", time.time())
        except Exception:
            duration = -1

        logger.info(
            "%s %s -> %s (%.3fs)",
            request.method,
            request.path,
            response.status_code,
            duration,
        )
        return response

    @app.route("/")
    def index():
        return {"message": "Bookstore API server is running."}

    return app
