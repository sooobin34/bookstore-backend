2) docs/db-schema.md (완성본)
# Database Schema (ERD · Table Specification)

본 문서는 Bookstore 서비스의 데이터베이스 테이블 구조를 설명합니다.

---

## 1. ERD 다이어그램
(여기에 db-schema.png 삽입)

---

## 2. 테이블 정의

### users
| 필드 | 타입 | 제약조건 |
|------|------|----------|
| user_id | INT PK | AUTO_INCREMENT |
| name | VARCHAR(100) | NOT NULL |
| email | VARCHAR(255) | UNIQUE NOT NULL |
| password | TEXT | NOT NULL |
| role | ENUM('USER','ADMIN') | DEFAULT 'USER' |
| is_active | BOOLEAN | DEFAULT TRUE |

---

### books
| 필드 | 타입 | 제약조건 |
|------|------|----------|
| book_id | INT PK | AUTO_INCREMENT |
| title | VARCHAR(255) | NOT NULL |
| author | VARCHAR(255) | NOT NULL |
| category | VARCHAR(50) | NULL |
| price | DECIMAL(10,2) | NOT NULL |
| stock | INT | NOT NULL |
| is_bestseller | BOOLEAN | DEFAULT FALSE |

---

### reviews
| 필드 | 타입 |
|------|-------|
| review_id | INT PK |
| user_id | INT FK → users |
| book_id | INT FK → books |
| rating | INT (1~5) |
| content | TEXT |
| likes_count | INT |

---

### cart_items
| 필드 |
|------|
| cart_item_id PK |
| user_id FK |
| book_id FK |
| quantity |

---

### orders
| 필드 |
|------|
| order_id PK |
| user_id FK |
| total_price |
| status (pending/completed) |

### order_items
| 필드 |
|------|
| item_id PK |
| order_id FK |
| book_id FK |
| quantity |
| price |

---

# 3. 관계 요약

- User (1) — (N) Reviews  
- User (1) — (N) Orders  
- User (1) — (N) CartItems  
- Book (1) — (N) Reviews  
- Order (1) — (N) OrderItems  

---