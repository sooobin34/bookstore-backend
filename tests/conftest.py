# tests/conftest.py
import os
import sys
import uuid

import pytest

# 👉 프로젝트 루트(= src 가 들어있는 디렉터리)를 sys.path 에 추가
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.app import create_app
from src.app.extensions import db  


@pytest.fixture
def app():
    """
    실제 create_app()을 사용하되,
    TESTING 모드 + 레이트리밋 비활성화 정도만 덮어쓴다.
    (기존 MySQL/RDS DB를 그대로 사용한다고 가정)
    """
    app = create_app()
    app.config.update(
        TESTING=True,
        RATELIMIT_ENABLED=False,
    )
    with app.app_context():
        yield app


@pytest.fixture
def client(app):
    """Flask 테스트 클라이언트"""
    return app.test_client()


# --------- 공통 헬퍼 ---------


def login(client, email, password):
    """주어진 이메일/비번으로 /auth/login 호출하고 토큰 반환"""
    resp = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    return data["accessToken"], data.get("refreshToken")


@pytest.fixture
def admin_tokens(client):
    """
    seed 데이터에 있는 ADMIN 계정
    email: testuser@example.com
    password: User123!
    """
    access, refresh = login(client, "testuser@example.com", "User123!")
    return {"access": access, "refresh": refresh}


@pytest.fixture
def admin_headers(admin_tokens):
    return {"Authorization": f"Bearer {admin_tokens['access']}"}


@pytest.fixture
def new_user_tokens(client):
    """
    매 테스트마다 새 USER를 하나 회원가입하고 토큰 발급.
    (이메일은 uuid로 매번 다르게)
    """
    unique_email = f"pytest_user_{uuid.uuid4().hex[:8]}@example.com"
    password = "User123!"

    # 회원가입
    resp = client.post(
        "/auth/signup",
        json={
            "name": "Pytest User",
            "email": unique_email,
            "password": password,
        },
    )
    assert resp.status_code == 201

    # 로그인
    access, refresh = login(client, unique_email, password)
    return {"access": access, "refresh": refresh, "email": unique_email}
