# src/api/wishlist.py

from flask import request
from flask_smorest import Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.orm import selectinload

from src.app.extensions import db
from src.app.models import Wishlist, Book
from src.app.common.response import make_response
from src.app.common.errors import error_response
from src.app.schemas.wishlist import WishlistCreateSchema, WishlistItemSchema
from src.app.schemas.common import ErrorSchema

blp = Blueprint(
    "Wishlist",
    __name__,
    url_prefix="/wishlist",
    description="Wishlist (찜 목록) APIs",
)


# -------------------------------------------------------------
# 1) 위시리스트에 도서 추가: POST /wishlist/items
# -------------------------------------------------------------
@blp.route("/items", methods=["POST"])
@jwt_required()
@blp.arguments(WishlistCreateSchema)
@blp.response(201, WishlistItemSchema)
@blp.alt_response(400, schema=ErrorSchema, description="입력 검증 실패 또는 도서 없음")
@blp.alt_response(401, schema=ErrorSchema, description="인증 실패")
def add_to_wishlist(body):
    """
    위시리스트에 도서를 추가한다.

    Request Body 예시:
    {
      "book_id": 1
    }
    """
    user_id = int(get_jwt_identity())
    book_id = body.get("book_id")

    # 1) 도서 존재 여부 체크
    book = Book.query.get(book_id)
    if not book:
        return error_response(
            status=404,
            code="BOOK_NOT_FOUND",
            message="Book not found",
            details={"book_id": book_id},
        ), 404

    # 2) 이미 위시리스트에 있는지 확인
    existing = Wishlist.query.filter_by(
        user_id=user_id,
        book_id=book_id,
    ).first()

    if existing:
        # 이미 존재하면 200으로 "이미 있음" 응답
        return make_response(
            "success",
            200,
            data={
                "wishlist_id": existing.wishlist_id,
                "book_id": existing.book_id,
                "user_id": existing.user_id,
                "created_at": existing.created_at.isoformat()
                if existing.created_at
                else None,
            },
            message="Already in wishlist",
        )

    # 3) 새로 추가
    wl = Wishlist(
        user_id=user_id,
        book_id=book_id,
    )
    db.session.add(wl)
    db.session.commit()

    return make_response(
        "success",
        201,
        data={
            "wishlist_id": wl.wishlist_id,
            "book_id": wl.book_id,
            "user_id": wl.user_id,
            "created_at": wl.created_at.isoformat()
            if wl.created_at
            else None,
        },
        message="Added to wishlist",
    )


# -------------------------------------------------------------
# 2) 내 위시리스트 전체 조회: GET /wishlist
# -------------------------------------------------------------
@blp.route("", methods=["GET"])
@jwt_required()
@blp.response(200)
@blp.alt_response(401, schema=ErrorSchema, description="인증 실패")
def list_my_wishlist():
    """
    내 위시리스트 전체 목록을 조회한다.
    Book 정보를 함께 내려준다.
    """
    user_id = int(get_jwt_identity())

    items = (
        Wishlist.query.options(selectinload(Wishlist.book))
        .filter_by(user_id=user_id)
        .order_by(Wishlist.created_at.desc())
        .all()
    )

    content = []
    for wl in items:
        book = wl.book
        content.append(
            {
                "wishlist_id": wl.wishlist_id,
                "book_id": wl.book_id,
                "user_id": wl.user_id,
                "created_at": wl.created_at.isoformat()
                if wl.created_at
                else None,
                "book": {
                    "book_id": book.book_id,
                    "title": book.title,
                    "author": book.author,
                    "price": float(book.price),
                    "category": book.category,
                    "isBestseller": book.is_bestseller,
                },
            }
        )

    return make_response(
        "success",
        200,
        data={"items": content, "count": len(content)},
        message="Wishlist fetched",
    )


# -------------------------------------------------------------
# 3) 개별 위시리스트 아이템 삭제: DELETE /wishlist/items/<id>
# -------------------------------------------------------------
@blp.route("/items/<int:wishlist_id>", methods=["DELETE"])
@jwt_required()
@blp.alt_response(401, schema=ErrorSchema, description="인증 실패")
@blp.alt_response(404, schema=ErrorSchema, description="위시리스트 아이템 없음")
def delete_wishlist_item(wishlist_id: int):
    """
    위시리스트 아이템을 wishlist_id 기준으로 삭제한다.
    """
    user_id = int(get_jwt_identity())

    wl = Wishlist.query.filter_by(
        wishlist_id=wishlist_id,
        user_id=user_id,
    ).first()

    if not wl:
        return error_response(
            status=404,
            code="WISHLIST_ITEM_NOT_FOUND",
            message="Wishlist item not found",
            details={"wishlist_id": wishlist_id},
        ), 404

    db.session.delete(wl)
    db.session.commit()

    return make_response(
        "success",
        200,
        data={"wishlist_id": wishlist_id},
        message="Wishlist item deleted",
    )


# -------------------------------------------------------------
# 4) 특정 도서를 위시리스트에서 제거: DELETE /wishlist/items/book/<book_id>
# -------------------------------------------------------------
@blp.route("/items/book/<int:book_id>", methods=["DELETE"])
@jwt_required()
@blp.alt_response(401, schema=ErrorSchema, description="인증 실패")
@blp.alt_response(404, schema=ErrorSchema, description="위시리스트에 해당 도서가 없음")
def delete_wishlist_item_by_book(book_id: int):
    """
    book_id 기준으로 내 위시리스트에서 제거한다.
    (이미지/카드 UI에서 '하트 토글' 구현할 때 유용한 패턴)
    """
    user_id = int(get_jwt_identity())

    wl = Wishlist.query.filter_by(
        user_id=user_id,
        book_id=book_id,
    ).first()

    if not wl:
        return error_response(
            status=404,
            code="WISHLIST_ITEM_NOT_FOUND",
            message="Wishlist item not found",
            details={"book_id": book_id},
        ), 404

    db.session.delete(wl)
    db.session.commit()

    return make_response(
        "success",
        200,
        data={"book_id": book_id},
        message="Wishlist item deleted by book_id",
    )


# -------------------------------------------------------------
# 5) 전체 위시리스트 비우기: DELETE /wishlist
# -------------------------------------------------------------
@blp.route("", methods=["DELETE"])
@jwt_required()
@blp.alt_response(401, schema=ErrorSchema, description="인증 실패")
def clear_wishlist():
    """
    내 위시리스트 전체 삭제.
    """
    user_id = int(get_jwt_identity())

    Wishlist.query.filter_by(user_id=user_id).delete()
    db.session.commit()

    return make_response(
        "success",
        200,
        data=None,
        message="Wishlist cleared",
    )
