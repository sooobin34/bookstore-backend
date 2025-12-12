# Bookstore REST API (웹서비스 설계 기말 프로젝트)

온라인 서점 도메인을 가진 RESTful 백엔드 API 서버입니다.  
도서 조회/검색, 장바구니, 주문, 리뷰, 위시리스트, 사용자 관리, JWT 인증/인가, 레이트 리밋, 로깅, Swagger 문서화까지 포함한 **풀스택 백엔드 과제** 구현을 목표로 합니다.

---

## 1. 프로젝트 개요

### 1-1. 문제 정의

- 사용자는 온라인 서점에서 도서를 검색하고 장바구니에 담은 뒤 주문을 생성할 수 있어야 한다.
- 사용자는 도서에 대한 리뷰/평점을 남기고, 관심 도서를 위시리스트에 저장할 수 있어야 한다.
- 관리자는 사용자/주문/도서 데이터를 관리하고, 관리자 전용 API를 사용할 수 있어야 한다.
- 모든 민감 정보(비밀번호, 토큰, DB 비밀번호)는 안전하게 관리되어야 하며, API는 일관된 에러 응답 포맷과 문서화를 제공해야 한다.

### 1-2. 주요 기능 요약

- **인증/인가**
  - 회원가입, 로그인, 토큰 재발급(JWT)
  - ROLE_USER / ROLE_ADMIN 기반 RBAC

- **유저(User)**
  - 내 정보 조회/수정 `/users/me`
  - 관리자 전용 사용자 목록 조회/역할 변경/계정 비활성화

- **도서(Book)**
  - 도서 목록 조회(검색/정렬/페이지네이션)
  - 도서 상세 조회
  - (관리자 전용 예정) 도서 생성/수정/삭제

- **리뷰(Review)**
  - 특정 도서의 리뷰 목록 조회 `/books/{bookId}/reviews`
  - 리뷰 작성/수정/삭제
  - 리뷰 검색(사용자/도서/평점 필터)

- **장바구니(Cart)**
  - 장바구니 아이템 추가/조회/수정/삭제/전체 비우기
  - 장바구니 요약(총 수량/총 금액)

- **주문(Order)**
  - 장바구니 → 주문 생성
  - 내 주문 목록/상세/취소
  - 관리자 전용 전체 주문 조회/상세/상태 변경(PENDING/PAID/CANCELED)

- **위시리스트(Wishlist)**
  - 위시리스트에 도서 추가/삭제
  - 내 위시리스트 목록 조회

- **공통**
  - 헬스체크 `/health`
  - Swagger UI `/swagger-ui`
  - 일관된 에러 응답 포맷
  - 레이트 리밋, CORS, 로깅

---

## 2. 실행 방법

### 2-1. 로컬 실행 (개발 환경)

### 1) 의존성 설치

```bash
# (선택) 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Windows PowerShell)
venv\Scripts\activate

# macOS / Linux
# source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt
```

### 2) 환경변수 설정 (.env 파일 생성)
```bash
# .env.example 복사 후 값 채우기
cp .env.example .env  # Windows에서는 수동 복사
```

.env 예시 (실제 비밀번호/키는 변경해서 사용):
```bash
FLASK_ENV=development

SECRET_KEY=change-me-secret
JWT_SECRET_KEY=change-me-jwt

SQLALCHEMY_DATABASE_URI=mysql+pymysql://root:your-password@127.0.0.1:3306/bookstore_db
SQLALCHEMY_TRACK_MODIFICATIONS=False

# JCloud 배포 시 참고용 (실제 값은 서버 .env에서 production 기준으로 설정)
JCLOUD_HOST=0.0.0.0
JCLOUD_PORT=8000

RATELIMIT_DEFAULT=100 per minute

API_TITLE=Bookstore API
API_VERSION=1.0.0

# CORS 허용 도메인(개발용)
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### 3) DB 마이그레이션 + 시드 데이터
```bash
# DB 마이그레이션 적용
flask db upgrade

# 시드 데이터 삽입 (200건 이상)
python seed_data.py
```

### 4) 서버 실행
```bash
flask run
# 기본: http://127.0.0.1:5000
```

---

## 2-2. JCloud 배포 (실서버)
JCloud 인스턴스(Ubuntu 24.04)에 동일한 코드를 배포하고, `systemd`로 Flask 서버를 실행/관리하도록 구성하였다.

### 1) JCloud 인스턴스 접속

- JCloud 대시보드에서 Ubuntu 24.04 인스턴스 생성
- SSH 접속 (예: Xshell 사용)

```bash
ssh -i <KEY>.pem ubuntu@<JCLOUD-HOST>
# 과제 환경에서는 학교에서 제공한 포트포워딩 엔드포인트(예: 113.198.66.75:포트)를 통해 접속
```

### 2) 코드 배포 및 의존성 설치
```bash
# 프로젝트 클론
git clone https://github.com/sooobin34/bookstore-backend
cd bookstore-backend

# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt
---
```

### 3) 서버용 .env (production) 설정

서버에서는 FLASK_ENV=production, JCloud 포트(8000) 기준으로 환경변수를 설정하였다.

```bash
FLASK_ENV=production

SECRET_KEY=********
JWT_SECRET_KEY=********

SQLALCHEMY_DATABASE_URI=mysql+pymysql://root:비밀번호@127.0.0.1:3306/bookstore_db
SQLALCHEMY_TRACK_MODIFICATIONS=False

JCLOUD_HOST=0.0.0.0
JCLOUD_PORT=8000

RATELIMIT_DEFAULT=100 per minute

API_TITLE=Bookstore API
API_VERSION=1.0.0
```

### 4) systemd 서비스 등록 (자동 실행)
```bash
sudo nano /etc/systemd/system/bookstore.service
```
```bash
[Unit]
Description=Bookstore Backend Flask Service
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/bookstore-backend
Environment="PATH=/home/ubuntu/bookstore-backend/venv/bin"
ExecStart=/home/ubuntu/bookstore-backend/venv/bin/python /home/ubuntu/bookstore-backend/run.py
Restart=always

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl daemon-reload
sudo systemctl enable bookstore
sudo systemctl start bookstore
sudo systemctl status bookstore
```

### 5) 헬스체크 및 배포 검증
```bash
curl http://127.0.0.1:8000/health
```

예시 응답:
```bash
{
  "service": "bookstore-backend",
  "status": "OK",
  "timestamp": "2025-12-06T15:02:00.020125+00:00",
  "version": "1.0.0"
}
```

- JCloud 인스턴스 재부팅 후에도 systemctl status bookstore 확인 시 active (running) 상태 유지

- /health 엔드포인트가 200 OK를 반환함을 통해 배포 상태를 검증하였다.

---

## 3. 환경변수 설명

.env.example 파일과 매칭되는 주요 환경변수:
| 키                                | 설명                                                     |
| -------------------------------- | ------------------------------------------------------ |
| `FLASK_ENV`                      | `development` / `production` 모드                        |
| `SECRET_KEY`                     | Flask 세션/보안용 비밀 키                                      |
| `JWT_SECRET_KEY`                 | JWT 발급/검증용 비밀 키                                        |
| `SQLALCHEMY_DATABASE_URI`        | MySQL 연결 정보 (`mysql+pymysql://user:pass@host:port/db`) |
| `SQLALCHEMY_TRACK_MODIFICATIONS` | SQLAlchemy 변경 추적 비활성화 플래그                              |
| `JCLOUD_HOST`                    | JCloud 서버 바인딩 IP (보통 `0.0.0.0`)                        |
| `JCLOUD_PORT`                    | JCloud 서버 포트 (본 프로젝트에서는 `8000`으로 사용)          |
| `RATELIMIT_DEFAULT`             | 기본 레이트 리밋 설정 (예: `100 per minute`)                   |
| `CORS_ORIGINS`                   | 허용할 Origin 리스트(쉼표 구분)                                  |
                                |

---

## 4. 배포/접속 정보

### 4-1. 로컬 환경
- Base URL: http://127.0.0.1:5000
- Swagger UI: http://127.0.0.1:5000/swagger-ui
- Health Check: http://127.0.0.1:5000/health

### 4-2. JCloud 환경 (외부 접속)
- SSH 접속(포트포워딩): `ssh -i bookstore.pem -p 19189 ubuntu@113.198.66.75`
- 외부 Base URL: `http://113.198.66.75:10189`  (내부 8000 포워딩)

- Health Check: `http://113.198.66.75:10189/health`
- Swagger UI: `http://113.198.66.75:10189/swagger-ui`
- OpenAPI JSON: `http://113.198.66.75:10189/openapi.json`

### (참고) 인스턴스 내부
- Internal Base URL: `http://10.0.0.189:8000`


---

## 5. 인증 플로우 (JWT)
### 5-1. 회원가입
```bash
POST /auth/signup
Content-Type: application/json

{
  "name": "Test User",
  "email": "test@example.com",
  "password": "Test123!"
}
```

### 5-2. 로그인 (Access / Refresh 발급)

```bash
POST /auth/login
Content-Type: application/json

{
  "email": "testuser@example.com",
  "password": "User123!"
}
```

성공 응답 예시
```bash
{
  "accessToken": "<JWT_ACCESS_TOKEN>",
  "refreshToken": "<JWT_REFRESH_TOKEN>",
  "tokenType": "Bearer"
}
```

### 5-3. 토큰 재발급
```bash
POST /auth/refresh
Authorization: Bearer <refreshToken>

→ 새로운 accessToken 발급
```

### 5-4. 보호된 엔드포인트 호출
```bash
GET /users/me
Authorization: Bearer <accessToken>
```

---

## 6. 역할/권한표 (RBAC)

| Role    | 설명           | 접근 가능한 주요 API 예시                         |
| ------- | ------------ | ---------------------------------------- |
| `USER`  | 일반 사용자       | 도서 조회, 장바구니, 주문 생성, 리뷰 작성/수정(본인)         |
| `ADMIN` | 관리자 (운영자 권한) | 사용자 목록/관리, 전체 주문 조회/상태 변경, 일부 관리자 전용 API |

관리자 전용 API 예시
- GET /users – 전체 사용자 목록 조회
- PATCH /users/{id}/role – 사용자 역할 변경
- PATCH /users/{id}/deactivate – 사용자 비활성화
- GET /orders/admin – 전체 주문 목록 조회
- GET /orders/admin/{order_id} – 특정 주문 상세 조회
- PATCH /orders/admin/{order_id}/status – 주문 상태 변경

---

## 7. 예제 계정 및 DB 정보
### 7-1. 예제 계정 (시드 데이터)
```bash
관리자(Admin)
email: admin@example.com
password: Admin123!

일반 사용자(User)
email: testuser@example.com
password: User123!
```

시드 스크립트(seed_data.py) 실행 시 Faker를 통해 추가 사용자, 도서, 리뷰, 주문, 장바구니, 위시리스트 데이터가 자동 생성됩니다.

### 7-2. DB 연결 정보 (테스트용)

- DB 타입: MySQL
- 호스트: 127.0.0.1
- 포트: 3306
- DB명: bookstore_db
- 계정/비밀번호: 별도 제출 문서에서 제공

---

## 8. 엔드포인트 요약

### 8-1. Health

- GET /health – 헬스체크(무인증, 200 OK)

### 8-2. Auth

- POST /auth/signup
- POST /auth/login
- POST /auth/refresh

### 8-3. Users

- GET /users/me – 내 정보 조회
- PATCH /users/me – 내 정보 수정
- GET /users – (ADMIN) 사용자 목록
- PATCH /users/{user_id}/role – (ADMIN) 역할 변경
- PATCH /users/{user_id}/deactivate – (ADMIN) 계정 비활성화

### 8-4. Books

- GET /books – 도서 목록 + 검색/정렬/페이지네이션
    - 쿼리 파라미터: page, size, sort, keyword, category, minPrice, maxPrice
- GET /books/{book_id} – 도서 상세
- POST /books – (ADMIN 예정) 도서 생성
- PATCH /books/{book_id} – (ADMIN 예정) 도서 수정
- DELETE /books/{book_id} – (ADMIN 예정) 도서 삭제

### 8-5. Reviews

- GET /books/{book_id}/reviews
- POST /books/{book_id}/reviews
- GET /reviews/{review_id}
- PATCH /reviews/{review_id}
- DELETE /reviews/{review_id}
- GET /reviews – 리뷰 검색 (userId, bookId, minRating, maxRating)

### 8-6. Cart

- POST /cart/items
- GET /cart/items
- PATCH /cart/items/{cart_item_id}
- DELETE /cart/items/{cart_item_id}
- DELETE /cart
- GET /cart/summary

### 8-7. Orders

- POST /orders – 장바구니 → 주문 생성
- GET /orders – 내 주문 목록
- GET /orders/{order_id} – 내 주문 상세
- PATCH /orders/{order_id}/cancel – 내 주문 취소

(ADMIN)
- GET /orders/admin
- GET /orders/admin/{order_id}
- PATCH /orders/admin/{order_id}/status

### 8-8. Wishlist

- GET /wishlist – 내 위시리스트 목록
- POST /wishlist – 위시리스트에 도서 추가
- DELETE /wishlist/{wishlist_id} – 위시리스트 아이템 삭제

---

## 9. 보안/성능 고려사항

### 9-1. 디버그 모드 비활성화 (배포 환경)

- 배포 환경에서는 Flask 애플리케이션을 `debug=False`로 실행하여
  디버그 콘솔(Werkzeug Debugger) 노출을 방지함
- 이를 통해 내부 스택트레이스 및 민감한 환경 정보 노출 위험을 최소화함

### 9-2. 비밀번호 해시

- bcrypt 기반 해시 함수 사용 (hash_password, verify_password)
- 비밀번호 평문 저장 금지

### 9-3. CORS

- Flask-CORS 사용
- 개발 환경: localhost:3000 등 허용
- 운영/배포 환경: 필요한 Origin만 허용하도록 .env에서 설정 가능

### 9-4. 레이트 리밋

- Flask-Limiter 사용
- 기본값: 100 per minute (전역)
- 옵션: .env의 RATELIMIT_DEFAULT로 조정 가능

### 9-5. N+1 방지

- Orders / Cart 등에서 joinedload, selectinload 사용
    - 예: 주문 목록에서 Order.items 및 OrderItem.book까지 Eager Loading
    - 장바구니 조회 시 CartItem.book을 Eager Loading

### 9-6. 로깅

- app.before_request / app.after_request에서 
    - HTTP 메서드, 경로, 상태코드, 응답 시간(ms) 로그 남김
- 예외 발생 시 Flask 기본 스택트레이스 + 커스텀 에러 응답

---

## 10. 테스트

- 테스트 러너: pytest
- 실행 명령어:
```bash
pytest -q
```

- 현재 테스트:
    - 총 20개 이상 (auth, books, cart/orders, users 등)
    - 성공/실패 케이스 포함
    - 인증이 필요한 엔드포인트에 대한 테스트 포함

---

## 11. Postman 컬렉션

- 제출 파일 예시:
    - postman/bookstore_collection.json
    - (필요 시) postman/bookstore_environment.json

### 11-1. 환경 변수

- {{BASE_URL}}
    - 로컬: http://127.0.0.1:5000
    - JCloud: http://<JCLOUD-IP>:<PORT>
- {{ACCESS_TOKEN}}, {{REFRESH_TOKEN}}
    - 로그인/리프레시 이후 Pre-request/Test 스크립트로 저장하여 자동으로 Authorization 헤더에 주입

### 11-2. Pre-request / Test 스크립트 예시

- 로그인 성공 시 accessToken / refreshToken을 환경 변수에 저장
- 보호된 API 호출 전 Authorization: Bearer {{ACCESS_TOKEN}} 자동 설정
- 응답 상태코드/필드 검증 (예: 200/201/400/401 등)

---

## 12. 한계와 개선 계획

- 현재 ADMIN 전용 도서 관리 API(create/update/delete)는 Swagger에는 정의되어 있으나, 실제 RBAC 강제(ADMIN만 허용)는 일부 주석 처리 상태 → 배포 이후 ADMIN 엔드포인트 완전 고정 예정

- 프론트엔드(React/Vue 등)는 포함되어 있지 않고, 향후 분리된 SPA 클라이언트와 연동할 계획

- 검색 기능은 기본적인 키워드/카테고리/가격 필터 위주로 구현되어 있으며, 향후 정렬 기준 추가(인기순, 리뷰순 등) 및 고급 검색(다중 카테고리, 태그) 확장 가능

- 주문/결제는 실제 PG 연동 없이 “상태 변경(PENDING/PAID/CANCELED)” 수준에서 시뮬레이션하며, 향후 외부 결제 모듈/웹훅 연동 여지 있음

---

## 13. 요약

이 프로젝트는 온라인 서점 비즈니스 로직을 가진 REST API 서버로서

- MySQL + SQLAlchemy + Flask-Migrate
- JWT 인증 + RBAC
- Swagger 자동 문서 + Postman 컬렉션
- 레이트리밋, CORS, 로깅, 표준화된 에러 응답
- 자동화 테스트(pytest)

까지 포함한 수업 요구사항에 맞춘 백엔드 종합 과제 구현입니다.
