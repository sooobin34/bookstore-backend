def test_add_item_to_cart_and_get_items(client, new_user_tokens):
    headers = {"Authorization": f"Bearer {new_user_tokens['access']}"}

    # 1) 장바구니에 책 1번 2권 추가
    resp = client.post(
        "/cart/items",
        headers=headers,
        json={"book_id": 1, "quantity": 2},
    )
    assert resp.status_code in (200, 201)
    data = resp.get_json()
    assert data["status"] == "success"

    # 2) 장바구니 조회해서 items 배열 확인
    resp2 = client.get("/cart/items", headers=headers)
    assert resp2.status_code == 200
    data2 = resp2.get_json()
    assert "items" in data2["data"]
    assert len(data2["data"]["items"]) >= 1


def test_cart_summary_matches_items(client, new_user_tokens):
    headers = {"Authorization": f"Bearer {new_user_tokens['access']}"}

    # 장바구니 초기화
    client.delete("/cart", headers=headers)

    # 책 1번 2권, 2번 1권 추가
    client.post("/cart/items", headers=headers, json={"book_id": 1, "quantity": 2})
    client.post("/cart/items", headers=headers, json={"book_id": 2, "quantity": 1})

    # 요약 호출
    resp = client.get("/cart/summary", headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["data"]["total_quantity"] >= 3  # 최소 3개 이상


def test_create_order_from_cart_and_cart_cleared(client, new_user_tokens):
    headers = {"Authorization": f"Bearer {new_user_tokens['access']}"}

    # 장바구니에 아이템 추가
    client.post("/cart/items", headers=headers, json={"book_id": 1, "quantity": 1})

    # 주문 생성
    resp = client.post("/orders", headers=headers, json={})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["status"] == "success"
    order_id = data["data"]["order_id"]

    # 장바구니가 비었는지 확인
    resp2 = client.get("/cart/items", headers=headers)
    assert resp2.status_code == 200
    data2 = resp2.get_json()
    assert len(data2["data"]["items"]) == 0

    # 주문 상세 조회도 한 번 확인
    resp3 = client.get(f"/orders/{order_id}", headers=headers)
    assert resp3.status_code == 200


def test_cancel_pending_order_success(client, new_user_tokens):
    headers = {"Authorization": f"Bearer {new_user_tokens['access']}"}

    # 장바구니 → 주문 하나 생성
    client.post("/cart/items", headers=headers, json={"book_id": 1, "quantity": 1})
    resp = client.post("/orders", headers=headers, json={})
    assert resp.status_code == 201
    order_id = resp.get_json()["data"]["order_id"]

    # 바로 취소 (PENDING 상태여야 함)
    resp2 = client.patch(f"/orders/{order_id}/cancel", headers=headers)
    assert resp2.status_code == 200
    data2 = resp2.get_json()
    assert data2["data"]["status"] == "CANCELED"


def test_cancel_non_pending_order_conflict(client, new_user_tokens):
    headers = {"Authorization": f"Bearer {new_user_tokens['access']}"}

    # 장바구니 → 주문 생성
    client.post("/cart/items", headers=headers, json={"book_id": 1, "quantity": 1})
    resp = client.post("/orders", headers=headers, json={})
    assert resp.status_code == 201
    order_id = resp.get_json()["data"]["order_id"]

    # ADMIN 권한으로 상태를 PAID로 바꾸기 위해 admin 로그인
    # (여기서는 간단하게 admin 계정으로 다시 로그인해서 사용)
    from tests.conftest import login

    admin_access, _ = login(client, "testuser@example.com", "User123!")
    admin_headers = {"Authorization": f"Bearer {admin_access}"}
    resp_admin = client.patch(
        f"/orders/admin/{order_id}/status",
        headers=admin_headers,
        json={"status": "PAID"},
    )
    assert resp_admin.status_code == 200

    # 이제 사용자 토큰으로 취소 시도 → STATE_CONFLICT 기대
    resp2 = client.patch(f"/orders/{order_id}/cancel", headers=headers)
    assert resp2.status_code == 409
    data2 = resp2.get_json()
    assert data2["code"] == "STATE_CONFLICT"


def test_admin_get_all_orders_requires_admin(client, new_user_tokens):
    # USER 토큰으로 /orders/admin 접근하면 403이어야 함
    headers = {"Authorization": f"Bearer {new_user_tokens['access']}"}
    resp = client.get("/orders/admin", headers=headers)
    assert resp.status_code == 403
    data = resp.get_json()
    assert data["code"] == "FORBIDDEN"


def test_admin_update_order_status_to_paid(client, admin_headers, new_user_tokens):
    # 1) USER로 주문 하나 만들기
    user_headers = {"Authorization": f"Bearer {new_user_tokens['access']}"}
    client.post("/cart/items", headers=user_headers, json={"book_id": 1, "quantity": 1})
    resp = client.post("/orders", headers=user_headers, json={})
    assert resp.status_code == 201
    order_id = resp.get_json()["data"]["order_id"]

    # 2) ADMIN이 상태를 PAID로 변경
    resp2 = client.patch(
        f"/orders/admin/{order_id}/status",
        headers=admin_headers,
        json={"status": "PAID"},
    )
    assert resp2.status_code == 200
    data2 = resp2.get_json()
    assert data2["data"]["status"] == "PAID"
