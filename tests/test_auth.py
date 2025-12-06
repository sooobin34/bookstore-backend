# tests/test_auth.py

def test_login_success(client):
    resp = client.post(
        "/auth/login",
        json={"email": "testuser@example.com", "password": "User123!"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert "accessToken" in data
    assert "refreshToken" in data
    assert data["tokenType"] == "Bearer"


def test_login_wrong_password(client):
    resp = client.post(
        "/auth/login",
        json={"email": "testuser@example.com", "password": "Wrong123!"},
    )
    # 우리의 구현은 401 + 표준 에러 응답 포맷
    assert resp.status_code == 401
    data = resp.get_json()
    assert data["code"] == "UNAUTHORIZED"


def test_refresh_success(client, admin_tokens):
    refresh = admin_tokens["refresh"]
    resp = client.post(
        "/auth/refresh",
        headers={"Authorization": f"Bearer {refresh}"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert "accessToken" in data
    assert data["tokenType"] == "Bearer"


def test_refresh_without_token(client):
    resp = client.post("/auth/refresh")
    assert resp.status_code == 401
    data = resp.get_json()

    # 우리 공통 에러 포맷에 맞게 체크
    assert data.get("code") == "UNAUTHORIZED"
    assert data.get("status") == 401
    assert "message" in data

