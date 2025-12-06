# API Design Document
Bookstore Backend — API Specification (최종 구현 기반)

---

### 1. Overview

- 본 문서는 Bookstore 서비스의 REST API 설계에 대한 최종 명세서입니다.
과제 1의 API 설계를 기반으로 실제 구현 과정에서 이루어진 변경·추가사항을 포함합니다.

리소스 구성:
- Auth: 로그인, 회원가입, 토큰 재발급
- Users: 사용자 조회, 비활성화(ADMIN), 내 정보 조회
- Books: 도서 조회, 검색, 베스트셀러 필터
- Reviews: 도서 리뷰 조회/작성
- Cart: 장바구니 아이템 추가/조회
- Orders: 주문 생성/조회/취소

---

### 2. Auth API

1. POST /auth/signup — 회원가입
Request
```bash
{
  "name": "string",
  "email": "email",
  "password": "User123!"
}
```

Response 201
```bash
{
  "userId": 32,
  "email": "user@example.com",
  "name": "New User"
}
```

2. POST /auth/login — 로그인
```bash
{
  "email": "user@example.com",
  "password": "User123!"
}
```

Response 200
```bash
{
  "accessToken": "jwt...",
  "refreshToken": "jwt..."
}
```

3. POST /auth/refresh — 토큰 재발급
헤더:
```bash
Authorization: Bearer <refreshToken>
```
---

### 3. Users API

1. GET /users/me
헤더: Authorization 필요

Response
```bash
{
  "userId": 31,
  "email": "testuser@example.com",
  "name": "Test User",
  "role": "ADMIN",
  "isActive": true
}
```

2. GET /users (ADMIN)
- 검색, 정렬, 페이지네이션 지원
```bash
GET /users?page=1&size=10&sort=createdAt,desc
```

3. PATCH /users/{id}/deactivate (ADMIN)
- 유저 비활성화 → LOGIN 불가

---

### 4. Books API
1. GET /books

검색 조건:
- title: 부분 검색
- category: Tech/Fiction/...
- min_price / max_price: 가격 범위
- is_bestseller: true/false
- sort: price,created_at

Response
```bash
{
  "content": [...],
  "page": 1,
  "size": 10,
  "totalElements": 60
}
```

2. GET /books/{id}
3. GET /books/{id}/reviews
- 도서 상세 페이지 하위 리소스

---

### 5. Reviews API
1. POST /books/{id}/reviews
(로그인 필요)

Payload:
```bash
{
  "rating": 5,
  "content": "Great book!"
}
```

---

### 6. Cart API
1. POST /cart/items
```bash
{
  "bookId": 1,
  "quantity": 2
}
```
2. GET /cart/items
- 현재 장바구니 리스트 조회

---

### 7. Orders API
1. POST /orders
- 장바구니 → 주문 생성
2. GET /orders/{id}
3. PATCH /orders/{id}/cancel
조건:
- 주문 상태가 pending일 때만 가능

---

### 8. Error Specification (표준 에러)

모든 에러는 아래 공통 포맷을 따른다.
```bash
{
  "timestamp": "2025-01-01T10:00:00Z",
  "path": "/books/999",
  "status": 404,
  "code": "RESOURCE_NOT_FOUND",
  "message": "Book not found"
}
```

사용된 에러 코드:
- BAD_REQUEST
- VALIDATION_FAILED
- UNAUTHORIZED
- TOKEN_EXPIRED
- FORBIDDEN
- USER_NOT_FOUND
- RESOURCE_NOT_FOUND
- DUPLICATE_RESOURCE
- STATE_CONFLICT
- INTERNAL_SERVER_ERROR

---

### 9. 변경 사항 요약 (과제1 → 실제 구현)

- Books 검색: category, bestseller 필터 추가
- Orders: total_price 자동 계산 로직 추가
- Users: deactivate 기능 → 로그인 불가 연동
- Reviews: likes_count 필드 추가
- Error Handling: Flask 공통 에러 핸들러로 통합