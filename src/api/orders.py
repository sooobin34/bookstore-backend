# src/api/orders.py

from functools import wraps
from flask import request
from flask_smorest import Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from src.app.extensions import db
from src.app.models import Order, OrderItem, CartItem, Book
from src.app.common.response import make_response
from src.app.common.errors import error_response
from src.app.schemas.order import OrderSchema, OrderCreateSchema
from src.app.schemas.common import ErrorSchema

blp = Blueprint(
    "Orders",
    __name__,
    url_prefix="/orders",
    description="Order APIs (주문 생성/조회/취소/관리자 처리)",
)


# -------------------------------------------------------------
# 공통 유틸
# -------------------------------------------------------------
def _parse_int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _get_pagination_params():
    """
    page, size, sort 쿼리 파라미터 처리
    sort 예) created_at,DESC | total_price,ASC
    """
    page = _parse_int(request.args.get("page", 1), 1)
    size = _parse_int(request.args.get("size", 10), 10)

    if page < 1:
        page = 1
    if size < 1:
        size = 10
    if size > 100:
        size = 100

    sort_param = request.args.get("sort", "created_at,DESC")
    field, direction = "created_at", "DESC"

    if "," in sort_param:
        parts = sort_param.split(",")
        if len(parts) == 2:
            field, direction = parts[0], parts[1].upper()

    field_map = {
        "created_at": Order.created_at,
        "total_price": Order.total_price,
        "status": Order.status,
    }

    sort_col = field_map.get(field, Order.created_at)
    sort_expr = sort_col.asc() if direction == "ASC" else sort_col.desc()

    return page, size, sort_param, sort_expr


def _serialize_order(order: Order, include_items=False):
    data = {
        "order_id": order.order_id,
        "user_id": order.user_id,
        "total_price": float(order.total_price),
        "status": order.status,
        "created_at": order.created_at.isoformat()
        if order.created_at else None,
    }

    if include_items:
        data["items"] = [
            {
                "order_item_id": item.order_item_id,
                "book_id": item.book_id,
                "quantity": item.quantity,
                "price": float(item.price),
            }
            for item in order.items
        ]

    return data


def admin_required(fn):
    """관리자 전용 데코레이터"""
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if claims.get("role") != "ADMIN":
            return error_response(
                status=403,
                code="FORBIDDEN",
                message="Admin role required",
            ), 403
        return fn(*args, **kwargs)

    return wrapper


# -------------------------------------------------------------
# 1) 주문 생성 POST /orders
# -------------------------------------------------------------
@blp.route("", methods=["POST"])
@blp.arguments(OrderCreateSchema)
@blp.response(201, OrderSchema)
@blp.alt_response(400, schema=ErrorSchema, description="장바구니 비어 있음")
@blp.alt_response(401, schema=ErrorSchema, description="로그인 필요")
@jwt_required()
def create_order(order_data):
    """
    현재 로그인한 사용자의 장바구니 → 주문 생성
    """
    user_id = int(get_jwt_identity())

    cart_rows = (
        CartItem.query
        .filter_by(user_id=user_id)
        .join(Book, CartItem.book_id == Book.book_id)
        .add_entity(Book)
        .all()
    )

    if not cart_rows:
        return error_response(
            status=400,
            code="CART_EMPTY",
            message="Cart is empty",
        ), 400

    total_price = sum(
        cart_item.quantity * float(book.price)
        for cart_item, book in cart_rows
    )

    order = Order(
        user_id=user_id,
        total_price=total_price,
        status="PENDING",
    )
    db.session.add(order)
    db.session.flush()  # order_id 확보

    for cart_item, book in cart_rows:
        db.session.add(
            OrderItem(
                order_id=order.order_id,
                book_id=book.book_id,
                quantity=cart_item.quantity,
                price=float(book.price),
            )
        )

    CartItem.query.filter_by(user_id=user_id).delete(
        synchronize_session=False
    )
    db.session.commit()

    return make_response(
        "success",
        201,
        data=_serialize_order(order, include_items=True),
        message="Order created",
    )


# -------------------------------------------------------------
# 2) 내 주문 목록 GET /orders
# -------------------------------------------------------------
@blp.route("", methods=["GET"])
@blp.response(200)
@blp.alt_response(401, schema=ErrorSchema, description="로그인 필요")
@jwt_required()
def get_my_orders():
    user_id = int(get_jwt_identity())
    page, size, sort_param, sort_expr = _get_pagination_params()

    q = (
        Order.query.options(joinedload(Order.items))
        .filter_by(user_id=user_id)
    )

    status_filter = request.args.get("status")
    if status_filter:
        q = q.filter(Order.status == status_filter)

    total = q.count()
    items = (
        q.order_by(sort_expr)
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    return make_response(
        "success",
        200,
        data={
            "content": [_serialize_order(o) for o in items],
            "page": page,
            "size": size,
            "totalElements": total,
            "totalPages": (total + size - 1) // size,
            "sort": sort_param,
        },
        message="My orders fetched",
    )


# -------------------------------------------------------------
# 3) 내 주문 상세 GET /orders/{id}
# -------------------------------------------------------------
@blp.route("/<int:order_id>", methods=["GET"])
@blp.alt_response(401, schema=ErrorSchema)
@blp.alt_response(404, schema=ErrorSchema)
@jwt_required()
def get_my_order_detail(order_id):
    user_id = int(get_jwt_identity())

    order = (
        Order.query.options(joinedload(Order.items))
        .filter_by(order_id=order_id, user_id=user_id)
        .first()
    )

    if not order:
        return error_response(
            status=404,
            code="ORDER_NOT_FOUND",
            message="Order not found",
        ), 404

    return make_response(
        "success",
        200,
        data=_serialize_order(order, include_items=True),
        message="Order detail fetched",
    )


# -------------------------------------------------------------
# 4) 주문 취소 PATCH /orders/{id}/cancel
# -------------------------------------------------------------
@blp.route("/<int:order_id>/cancel", methods=["PATCH"])
@jwt_required()
def cancel_order(order_id):
    user_id = int(get_jwt_identity())

    order = Order.query.filter_by(
        order_id=order_id,
        user_id=user_id,
    ).first()

    if not order:
        return error_response(
            status=404,
            code="ORDER_NOT_FOUND",
            message="Order not found",
        ), 404

    if order.status != "PENDING":
        return error_response(
            status=409,
            code="STATE_CONFLICT",
            message="Only PENDING orders can be cancelled",
        ), 409

    order.status = "CANCELED"
    db.session.commit()

    return make_response(
        "success",
        200,
        data=_serialize_order(order, True),
        message="Order cancelled",
    )


# -------------------------------------------------------------
# 5) 관리자 전체 주문 조회 GET /orders/admin
# -------------------------------------------------------------
@blp.route("/admin", methods=["GET"])
@admin_required
def get_all_orders_admin():
    page, size, sort_param, sort_expr = _get_pagination_params()

    q = Order.query.options(joinedload(Order.items))

    total = q.count()
    items = (
        q.order_by(sort_expr)
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    return make_response(
        "success",
        200,
        data={
            "content": [_serialize_order(o) for o in items],
            "page": page,
            "size": size,
            "totalElements": total,
            "totalPages": (total + size - 1) // size,
            "sort": sort_param,
        },
        message="All orders fetched",
    )


# -------------------------------------------------------------
# 6) 관리자 주문 상세 GET /orders/admin/{id}
# -------------------------------------------------------------
@blp.route("/admin/<int:order_id>", methods=["GET"])
@admin_required
def get_order_detail_admin(order_id):
    order = (
        Order.query.options(joinedload(Order.items))
        .filter_by(order_id=order_id)
        .first()
    )

    if not order:
        return error_response(
            status=404,
            code="ORDER_NOT_FOUND",
            message="Order not found",
        ), 404

    return make_response(
        "success",
        200,
        data=_serialize_order(order, include_items=True),
        message="Order detail fetched (admin)",
    )


# -------------------------------------------------------------
# 7) 관리자 주문 상태 변경 PATCH /orders/admin/{id}/status
# -------------------------------------------------------------
@blp.route("/admin/<int:order_id>/status", methods=["PATCH"])
@admin_required
def update_order_status(order_id):
    data = request.get_json() or {}
    new_status = data.get("status")

    if new_status not in ("PENDING", "PAID", "CANCELED"):
        return error_response(
            status=400,
            code="INVALID_ORDER_STATUS",
            message="Invalid order status",
        ), 400

    order = Order.query.get(order_id)
    if not order:
        return error_response(
            status=404,
            code="ORDER_NOT_FOUND",
            message="Order not found",
        ), 404

    order.status = new_status
    db.session.commit()

    return make_response(
        "success",
        200,
        data=_serialize_order(order, True),
        message="Order status updated",
    )
