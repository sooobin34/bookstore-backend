# src/api/books.py

from flask import request, jsonify
from flask_smorest import Blueprint
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy import or_

from src.app.extensions import db
from src.app.models import Book
from src.app.common.errors import error_response
from src.app.schemas.book import BookCreateSchema, BookSchema
from src.app.schemas.common import ErrorSchema

blp = Blueprint(
    "Books",
    __name__,
    url_prefix="/books",
    description="Book browsing & admin CRUD APIs",
)


# -------------------------------------------
# Helpers
# -------------------------------------------
def parse_pagination_args():
    try:
        page = int(request.args.get("page", 1))
        size = int(request.args.get("size", 20))
    except ValueError:
        return None, None, error_response(
            status=400,
            code="INVALID_QUERY_PARAM",
            message="page and size must be integers",
        )

    if page < 1:
        page = 1
    if size < 1:
        size = 1
    if size > 100:
        size = 100

    return page, size, None


def parse_sort_arg():
    sort_raw = request.args.get("sort", "created_at,DESC")
    parts = sort_raw.split(",")

    field = parts[0] if parts[0] else "created_at"
    direction = parts[1].upper() if len(parts) > 1 else "DESC"

    # Book 모델에서 해당하는 컬럼 찾기
    column = getattr(Book, field, None)
    if column is None:
        column = Book.created_at  # 기본값

    if direction == "ASC":
        return sort_raw, column.asc()
    return sort_raw, column.desc()


def require_admin():
    """RBAC: 관리자 전용 엔드포인트 검사"""
    claims = get_jwt()
    if claims.get("role") != "ADMIN":
        return error_response(
            status=403,
            code="FORBIDDEN",
            message="Admin only endpoint.",
        )
    return None


# -------------------------------------------
# GET /books — 도서 목록
# -------------------------------------------
@blp.route("", methods=["GET"])
@blp.response(200)
@blp.alt_response(400, schema=ErrorSchema, description="잘못된 요청 파라미터")
@blp.alt_response(500, schema=ErrorSchema, description="서버 오류")
def list_books():
    """
    도서 목록 조회 + 검색(keyword), 카테고리, 가격 범위,
    정렬(sort), 페이지네이션(page,size)
    """
    page, size, err = parse_pagination_args()
    if err:
        return err, 400

    sort_str, sort_column = parse_sort_arg()

    keyword = request.args.get("keyword")
    category = request.args.get("category")
    min_price = request.args.get("minPrice")
    max_price = request.args.get("maxPrice")

    query = Book.query

    if keyword:
        word = f"%{keyword}%"
        query = query.filter(or_(Book.title.ilike(word), Book.author.ilike(word)))

    if category:
        query = query.filter(Book.category == category)

    try:
        if min_price is not None:
            query = query.filter(Book.price >= float(min_price))
        if max_price is not None:
            query = query.filter(Book.price <= float(max_price))
    except ValueError:
        return error_response(
            status=400,
            code="INVALID_QUERY_PARAM",
            message="minPrice and maxPrice must be numbers",
        ), 400

    query = query.order_by(sort_column)

    pagination = query.paginate(page=page, per_page=size, error_out=False)

    content = [
        {
            "bookId": b.book_id,
            "title": b.title,
            "author": b.author,
            "category": b.category,
            "price": float(b.price),
            "stock": b.stock,
            "isBestseller": b.is_bestseller,
            "description": b.description,
            "imageUrl": b.image_url,
            "createdAt": b.created_at.isoformat() if b.created_at else None,
        }
        for b in pagination.items
    ]

    return jsonify(
        {
            "content": content,
            "page": page,
            "size": size,
            "totalElements": pagination.total,
            "totalPages": pagination.pages,
            "sort": sort_str,
        }
    )


# -------------------------------------------
# GET /books/{id} — 단일 도서 조회
# -------------------------------------------
@blp.route("/<int:book_id>", methods=["GET"])
@blp.response(200, BookSchema)
@blp.alt_response(404, schema=ErrorSchema, description="도서 없음")
def get_book(book_id: int):
    book = Book.query.get(book_id)
    if not book:
        return error_response(
            status=404,
            code="RESOURCE_NOT_FOUND",
            message=f"Book {book_id} not found",
        ), 404

    return {
        "bookId": book.book_id,
        "title": book.title,
        "author": book.author,
        "category": book.category,
        "price": float(book.price),
        "stock": book.stock,
        "isBestseller": book.is_bestseller,
        "description": book.description,
        "imageUrl": book.image_url,
    }


# -------------------------------------------
# POST /books — 도서 생성(관리자)
# -------------------------------------------
@blp.route("", methods=["POST"])
@jwt_required()
@blp.arguments(BookCreateSchema)
@blp.response(201, BookSchema)
@blp.alt_response(400, schema=ErrorSchema)
@blp.alt_response(403, schema=ErrorSchema, description="관리자 권한 없음")
def create_book(data):
    """
    도서 등록 (ADMIN 전용)
    """
    # 관리자 제한
    # admin_err = require_admin()
    # if admin_err:
    #     return admin_err, 403

    try:
        price = float(data["price"])
        stock = int(data["stock"])
    except Exception:
        return error_response(
            status=400,
            code="VALIDATION_FAILED",
            message="price must be number and stock must be integer",
        ), 400

    book = Book(
        title=data["title"],
        author=data["author"],
        category=data["category"],
        price=price,
        stock=stock,
        is_bestseller=data.get("isBestseller", False),
        description=data.get("description"),
        image_url=data.get("imageUrl"),
    )

    db.session.add(book)
    db.session.commit()

    return {
        "bookId": book.book_id,
        "title": book.title,
        "author": book.author,
        "category": book.category,
        "price": float(book.price),
        "stock": book.stock,
        "isBestseller": book.is_bestseller,
        "description": book.description,
        "imageUrl": book.image_url,
    }


# -------------------------------------------
# PATCH /books/{id} — 도서 수정
# -------------------------------------------
@blp.route("/<int:book_id>", methods=["PATCH"])
@jwt_required(optional=True)
@blp.alt_response(404, schema=ErrorSchema)
@blp.alt_response(400, schema=ErrorSchema)
def update_book(book_id: int):
    book = Book.query.get(book_id)
    if not book:
        return error_response(
            status=404,
            code="RESOURCE_NOT_FOUND",
            message=f"Book {book_id} not found",
        ), 404

    data = request.get_json() or {}

    if "title" in data:
        book.title = data["title"]
    if "author" in data:
        book.author = data["author"]
    if "category" in data:
        book.category = data["category"]
    if "price" in data:
        try:
            book.price = float(data["price"])
        except ValueError:
            return error_response(
                status=400,
                code="VALIDATION_FAILED",
                message="price must be number",
            ), 400
    if "stock" in data:
        try:
            book.stock = int(data["stock"])
        except ValueError:
            return error_response(
                status=400,
                code="VALIDATION_FAILED",
                message="stock must be integer",
            ), 400
    if "isBestseller" in data:
        book.is_bestseller = bool(data["isBestseller"])
    if "description" in data:
        book.description = data["description"]
    if "imageUrl" in data:
        book.image_url = data["imageUrl"]

    db.session.commit()

    return jsonify({"bookId": book.book_id})


# -------------------------------------------
# DELETE /books/{id}
# -------------------------------------------
@blp.route("/<int:book_id>", methods=["DELETE"])
@jwt_required(optional=True)
@blp.alt_response(404, schema=ErrorSchema)
def delete_book(book_id: int):
    book = Book.query.get(book_id)
    if not book:
        return error_response(
            status=404,
            code="RESOURCE_NOT_FOUND",
            message=f"Book {book_id} not found",
        ), 404

    db.session.delete(book)
    db.session.commit()

    return "", 204
