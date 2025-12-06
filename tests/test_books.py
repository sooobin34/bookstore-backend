def test_get_books_list_basic(client):
    resp = client.get("/books")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "content" in data
    assert isinstance(data["content"], list)
    assert "page" in data
    assert "size" in data
    assert "totalElements" in data


def test_get_books_with_keyword_search(client):
    resp = client.get("/books?keyword=the")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "content" in data


def test_get_book_detail_not_found(client):
    # 존재하지 않을 것 같은 큰 ID
    resp = client.get("/books/999999")
    # 우리 에러 핸들러에 따라 404 + 표준 에러 응답 포맷
    assert resp.status_code == 404
    data = resp.get_json()
    assert data["code"] in ("RESOURCE_NOT_FOUND", "BOOK_NOT_FOUND")


def test_get_book_reviews_subresource(client):
    # book_id=1은 seed 데이터에 있다고 가정
    resp = client.get("/books/1/reviews")
    # 책이 없어도 404, 있으면 200
    assert resp.status_code in (200, 404)
    if resp.status_code == 200:
        data = resp.get_json()
        assert "bookId" in data
        assert "content" in data
        assert isinstance(data["content"], list)


def test_admin_create_book_validation_error(client, admin_headers):
    # 필수 필드(title 등)를 일부러 빼서 400/422 유도
    resp = client.post(
        "/books",
        headers=admin_headers,
        json={
            "title": "",
            "author": "",
            # price, stock 등 빼먹기
        },
    )
    assert resp.status_code in (400, 422)
