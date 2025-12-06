import os
from dotenv import load_dotenv

# 프로젝트 루트의 .env 읽기
# (run.py를 프로젝트 루트에서 실행한다고 가정)
load_dotenv()

class Config:
    # 기본 Flask 설정
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = FLASK_ENV == "development"
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")

    # DB 설정 (없으면 sqlite dev.db 사용)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "SQLALCHEMY_DATABASE_URI",
        "sqlite:///dev.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT 설정
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-jwt")

    # Flask-Smorest / Swagger 설정
    API_TITLE = "Bookstore API"
    API_VERSION = "v1"
    OPENAPI_VERSION = "3.0.3"
    OPENAPI_URL_PREFIX = "/"
    OPENAPI_SWAGGER_UI_PATH = "/docs"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

    # Rate Limit (나중에 조절 가능)
    RATELIMIT_DEFAULT = "100 per minute"
