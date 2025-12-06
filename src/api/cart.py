# src/api/cart.py

from flask_smorest import Blueprint
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from sqlalchemy.orm import selectinload

from src.app.extensions import db
from src.app.models import CartItem, Book
from src.app.common.response import make_response
from src.app.common.errors import error_response
from src.app.schemas.cart import CartCreateSchema, CartItemSchema
from src.app.schemas.common import ErrorSchema

blp = Blueprint(
    "Cart",
    __name__,
    url_prefix="/cart",
    description="Cart operations (장바구니 추가/조회/수정/삭제)",
)


def _parse_int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


# -------------------------------------------------------------
# 1) 장바구니 아이템 추가: POST /cart/items
# -------------------------------------------------------------
@blp.route("/items", methods=["POST"])
@blp.arguments(CartCreateSchema)
@blp.response(201, description="장바구니에 상품 추가 성공")
@blp.alt_response(400, schema=ErrorSchema, description="잘못된 입력 값")
@blp.alt_response(401, schema=ErrorSchema, description="로그인 필요")
@blp.alt_response(404, schema=ErrorSchema, description="도서를 찾을 수 없음")
@jwt_required()
def add_cart_item(data):
    """
    장바구니에 도서 추가

    요청 예시:
    {
        "book_id": 1,
        "quantity": 2
    }
    """
    user_id = int(get_jwt_identity())

    book_id = data.get("book_id")
    quantity = data.get("quantity", 1)

    book = Book.query.get(book_id)
    if not book:
        return error_response(
            status=404,
            code="BOOK_NOT_FOUND",
            message="Book not found",
            details={"book_id": book_id},
        ), 404

    cart_item = CartItem.query.filter_by(user_id=user_id, book_id=book_id).first()

    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(
            user_id=user_id,
            book_id=book_id,
            quantity=quantity,
        )
        db.session.add(cart_item)

    db.session.commit()

    return make_response(
        "success",
        201,
        data={
            "cart_item_id": cart_item.cart_item_id,
            "book_id": cart_item.book_id,
            "quantity": cart_item.quantity,
        },
        message="Item added to cart",
    )


# -------------------------------------------------------------
# 2) 내 장바구니 조회 GET /cart/items
# -------------------------------------------------------------
@blp.route("/items", methods=["GET"])
@blp.response(200, description="내 장바구니 목록 조회")
@blp.alt_response(401, schema=ErrorSchema, description="로그인 필요")
@jwt_required()
def get_cart_items():
    """
    현재 로그인한 사용자의 장바구니 목록 조회
    """
    user_id = int(get_jwt_identity())

    items = (
        CartItem.query.options(selectinload(CartItem.book))
        .filter_by(user_id=user_id)
        .order_by(CartItem.created_at.desc())
        .all()
    )

    content = []
    for item in items:
        book = item.book
        content.append(
            {
                "cart_item_id": item.cart_item_id,
                "book_id": item.book_id,
                "quantity": item.quantity,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "book": {
                    "book_id": book.book_id,
                    "title": book.title,
                    "author": book.author,
                    "price": float(book.price),
                },
            }
        )

    return make_response(
        "success",
        200,
        data={"items": content},
        message="Cart items fetched",
    )


# -------------------------------------------------------------
# 3) 장바구니 수량 수정 PATCH /cart/items/<id>
# -------------------------------------------------------------
@blp.route("/items/<int:cart_item_id>", methods=["PATCH"])
@blp.response(200, description="장바구니 수량 수정 성공")
@blp.alt_response(400, schema=ErrorSchema, description="수량이 유효하지 않음")
@blp.alt_response(401, schema=ErrorSchema, description="로그인 필요")
@blp.alt_response(404, schema=ErrorSchema, description="장바구니 아이템 없음")
@jwt_required()
def update_cart_item(cart_item_id):
    """
    장바구니 아이템 수량 수정
    """
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}

    quantity = data.get("quantity")
    quantity = _parse_int(quantity, None)

    if not quantity or quantity <= 0:
        return error_response(
            status=400,
            code="CART_INVALID_QUANTITY",
            message="quantity must be a positive integer",
        ), 400

    cart_item = CartItem.query.filter_by(
        cart_item_id=cart_item_id,
        user_id=user_id,
    ).first()

    if not cart_item:
        return error_response(
            status=404,
            code="CART_ITEM_NOT_FOUND",
            message="Cart item not found",
            details={"cart_item_id": cart_item_id},
        ), 404

    cart_item.quantity = quantity
    db.session.commit()

    return make_response(
        "success",
        200,
        data={
            "cart_item_id": cart_item.cart_item_id,
            "book_id": cart_item.book_id,
            "quantity": cart_item.quantity,
        },
        message="Cart item updated",
    )


# -------------------------------------------------------------
# 4) 아이템 삭제 DELETE /cart/items/<id>
# -------------------------------------------------------------
@blp.route("/items/<int:cart_item_id>", methods=["DELETE"])
@blp.response(200, description="장바구니 아이템 삭제 성공")
@blp.alt_response(401, schema=ErrorSchema, description="로그인 필요")
@blp.alt_response(404, schema=ErrorSchema, description="장바구니 아이템 없음")
@jwt_required()
def delete_cart_item(cart_item_id):
    """
    개별 장바구니 아이템 삭제
    """
    user_id = int(get_jwt_identity())

    cart_item = CartItem.query.filter_by(
        cart_item_id=cart_item_id,
        user_id=user_id,
    ).first()

    if not cart_item:
        return error_response(
            status=404,
            code="CART_ITEM_NOT_FOUND",
            message="Cart item not found",
        ), 404

    db.session.delete(cart_item)
    db.session.commit()

    return make_response(
        "success",
        200,
        data={"cart_item_id": cart_item_id},
        message="Cart item deleted",
    )


# -------------------------------------------------------------
# 5) 전체 비우기 DELETE /cart
# -------------------------------------------------------------
@blp.route("", methods=["DELETE"])
@blp.response(200, description="장바구니 전체 비우기 성공")
@blp.alt_response(401, schema=ErrorSchema, description="로그인 필요")
@jwt_required()
def clear_cart():
    """
    현재 사용자의 장바구니 전체 비우기
    """
    user_id = int(get_jwt_identity())

    CartItem.query.filter_by(user_id=user_id).delete()
    db.session.commit()

    return make_response(
        "success",
        200,
        data=None,
        message="Cart cleared",
    )


# -------------------------------------------------------------
# 6) 요약 GET /cart/summary
# -------------------------------------------------------------
@blp.route("/summary", methods=["GET"])
@blp.response(200, description="장바구니 요약(수량/총합) 조회")
@blp.alt_response(401, schema=ErrorSchema, description="로그인 필요")
@jwt_required()
def get_cart_summary():
    """
    장바구니 요약 정보 (총 수량, 총 금액) 조회
    """
    user_id = int(get_jwt_identity())

    result = (
        db.session.query(
            func.coalesce(func.sum(CartItem.quantity), 0).label("total_quantity"),
            func.coalesce(
                func.sum(CartItem.quantity * Book.price), 0
            ).label("total_price"),
        )
        .join(Book, CartItem.book_id == Book.book_id)
        .filter(CartItem.user_id == user_id)
        .first()
    )

    total_quantity = int(result.total_quantity or 0)
    total_price = float(result.total_price or 0)

    return make_response(
        "success",
        200,
        data={
            "total_quantity": total_quantity,
            "total_price": total_price,
        },
        message="Cart summary fetched",
    )
