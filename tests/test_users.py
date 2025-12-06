def test_get_me_success(client, admin_headers):
    resp = client.get("/users/me", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["email"] == "testuser@example.com"
    assert data["role"] in ("ADMIN", "USER")


def test_get_me_unauthorized(client):
    resp = client.get("/users/me")
    assert resp.status_code == 401
    data = resp.get_json()

    assert data.get("code") == "UNAUTHORIZED"
    assert data.get("status") == 401
    assert "message" in data


def test_admin_get_users_list(client, admin_headers):
    resp = client.get("/users", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    # 페이지네이션 구조라고 가정 (content 배열)
    assert "content" in data
    assert isinstance(data["content"], list)


def test_non_admin_get_users_forbidden(client, new_user_tokens):
    headers = {"Authorization": f"Bearer {new_user_tokens['access']}"}
    resp = client.get("/users", headers=headers)
    # RBAC에 의해 FORBIDDEN 이어야 함
    assert resp.status_code in (403, 401)
    # 403인 경우만 에러 코드 체크
    if resp.status_code == 403:
        data = resp.get_json()
        assert data["code"] == "FORBIDDEN"


def test_admin_deactivate_user_and_login_fails(client, admin_headers, new_user_tokens):
    # 1) 방금 만든 USER의 이메일 가져오기
    email = new_user_tokens["email"]

    # 2) /users?keyword= 같은 검색이 없다고 가정 → DB에서 직접 찾기보다는
    #    관리자 API 중 /users 에서 content 중에 해당 이메일 찾기
    resp = client.get("/users", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    target_user_id = None
    for u in data.get("content", []):
        if u.get("email") == email:
            target_user_id = u.get("userId") or u.get("user_id")
            break

    assert target_user_id is not None

    # 3) 비활성화 호출
    resp2 = client.patch(f"/users/{target_user_id}/deactivate", headers=admin_headers)
    assert resp2.status_code in (200, 204)

    # 4) 다시 로그인 시도 
    access = new_user_tokens["access"]
    headers_user = {"Authorization": f"Bearer {access}"}
    resp3 = client.get("/users/me", headers=headers_user)
    assert resp3.status_code == 403
    data3 = resp3.get_json()
    assert data3["code"] == "FORBIDDEN"
