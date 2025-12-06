# Architecture Overview  
Bookstore Backend — System Architecture Document

---

## 1. 전체 시스템 구조

프로젝트는 Flask Application Factory 패턴을 기반으로 구성되며 다음과 같은 계층 구조를 가진다:
```bash
src/
├─ app/
│ ├─ init.py # create_app()
│ ├─ extensions.py # db, migrate, jwt, limiter 초기화
│ ├─ models.py # SQLAlchemy 모델 정의
│ ├─ security.py # JWT, 비밀번호 해싱
│ └─ common/
│ └─ errors.py # 표준 에러 핸들링
├─ api/
│ ├─ auth.py
│ ├─ users.py
│ ├─ books.py
│ ├─ reviews.py
│ ├─ cart.py
│ └─ orders.py
└─ scripts/
└─ seed.py
```


---

## 2. Application Factory (create_app)

- 환경 변수 로딩
- DB, JWT, RateLimit, Swagger 초기화
- Blueprint 등록
- 에러 핸들러 등록

**장점:**  
- 테스트 용이(pytest에서 create_app 호출 가능)  
- 확장성 좋음  
- 환경별 설정(dev/prod) 분리 가능  

---

## 3. Extensions 구조

| 모듈 | 역할 |
|------|------|
| SQLAlchemy | ORM + DB 세션 |
| Marshmallow | Request/Response Validation |
| JWTManager | 인증/인가 |
| Limiter | Rate Limit |
| APISpec | Swagger 문서 생성 |

---

## 4. Routing / Blueprint 구조

각 도메인은 독립된 Blueprint로 분리됨.

예:  
```bash
/auth → auth.py
/users → users.py
/books → books.py
/orders → orders.py
```

---

## 5. Error Handling Layer

모든 예외는 common/errors.py에서 중앙 처리:

- ValidationError
- 404/401/403/422 등 표준 에러 코드 매핑
- JSON 포맷 통일

---

## 6. Authentication / RBAC 설계

- JWT access + refresh token 구조
- 역할 기반 접근 제어(RBAC)
  - USER: 기본 API 접근 가능
  - ADMIN: /users 관리, 주문 상태 변경 가능

---

## 7. 테스트 구조

- pytest 사용
- conftest.py에서 create_app + 테스트 DB 연결
- 토큰 자동 발급 헬퍼 제공(login 함수)
- 총 20개 이상 테스트 통과

---

## 8. 배포 구조(JCloud)

- Gunicorn + PM2 조합  
- 서버 재시작 후 자동 실행  
- Health Check: `/health` 200 OK  

---
