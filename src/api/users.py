# src/api/users.py

from flask import jsonify, request
from flask_smorest import Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from src.app.extensions import db
from src.app.models import User
from src.app.common.errors import error_response
from src.app.schemas.common import ErrorSchema

blp = Blueprint(
    "Users",
    __name__,
    url_prefix="/users",
    description="User profile & admin APIs",
)


def require_admin():
    """
    RBAC: ADMIN 전용 엔드포인트에서 사용
    """
    claims = get_jwt()
    role = claims.get("role")
    if role != "ADMIN":
        return error_response(
            status=403,
            code="FORBIDDEN",
            message="Admin only endpoint.",
        )
    return None


# -------------------------------------------------
# 1) 내 정보 조회 / 수정
#    GET /users/me
#    PATCH /users/me
# -------------------------------------------------
@blp.route("/me", methods=["GET"])
@jwt_required()
@blp.alt_response(401, schema=ErrorSchema, description="인증 실패")
@blp.alt_response(403, schema=ErrorSchema, description="비활성 사용자")
@blp.alt_response(404, schema=ErrorSchema, description="사용자 없음")
def get_me():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return error_response(
            status=404,
            code="USER_NOT_FOUND",
            message="User not found",
        ), 404

    if not user.is_active:
        return error_response(
            status=403,
            code="FORBIDDEN",
            message="User is deactivated",
        ), 403

    return jsonify(
        {
            "userId": user.user_id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "isActive": user.is_active,
        }
    )


@blp.route("/me", methods=["PATCH"])
@jwt_required()
@blp.alt_response(400, schema=ErrorSchema, description="입력 검증 실패")
@blp.alt_response(401, schema=ErrorSchema, description="인증 실패")
@blp.alt_response(403, schema=ErrorSchema, description="비활성 사용자")
@blp.alt_response(404, schema=ErrorSchema, description="사용자 없음")
def update_me():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return error_response(
            status=404,
            code="USER_NOT_FOUND",
            message="User not found",
        ), 404

    if not user.is_active:
        return error_response(
            status=403,
            code="FORBIDDEN",
            message="User is deactivated",
        ), 403

    data = request.get_json() or {}

    if "name" in data:
        if not isinstance(data["name"], str) or not data["name"].strip():
            return error_response(
                status=400,
                code="VALIDATION_FAILED",
                message="name must be non-empty string",
            ), 400
        user.name = data["name"].strip()

    db.session.commit()

    return jsonify(
        {
            "userId": user.user_id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "isActive": user.is_active,
        }
    )


# -------------------------------------------------
# 2) 관리자 전용 API
#    - GET /users
#    - PATCH /users/{id}/role
#    - PATCH /users/{id}/deactivate
# -------------------------------------------------
@blp.route("", methods=["GET"])
@jwt_required()
@blp.alt_response(400, schema=ErrorSchema, description="페이지네이션 파라미터 오류")
@blp.alt_response(401, schema=ErrorSchema, description="인증 실패")
@blp.alt_response(403, schema=ErrorSchema, description="관리자 권한 없음")
def list_users():
    admin_err = require_admin()
    if admin_err:
        return admin_err, 403

    # 간단 페이지네이션 (users도 page/size 지원)
    try:
        page = int(request.args.get("page", 1))
        size = int(request.args.get("size", 20))
    except ValueError:
        return error_response(
            status=400,
            code="INVALID_QUERY_PARAM",
            message="page and size must be integers",
        ), 400

    if page < 1:
        page = 1
    if size < 1:
        size = 1
    if size > 100:
        size = 100

    query = User.query.order_by(User.created_at.desc())
    pagination = query.paginate(page=page, per_page=size, error_out=False)

    content = []
    for user in pagination.items:
        content.append(
            {
                "userId": user.user_id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "isActive": user.is_active,
                "createdAt": user.created_at.isoformat() if user.created_at else None,
            }
        )

    return jsonify(
        {
            "content": content,
            "page": page,
            "size": size,
            "totalElements": pagination.total,
            "totalPages": pagination.pages,
        }
    )


@blp.route("/<int:user_id>/role", methods=["PATCH"])
@jwt_required()
@blp.alt_response(400, schema=ErrorSchema, description="역할 값 잘못됨")
@blp.alt_response(401, schema=ErrorSchema, description="인증 실패")
@blp.alt_response(403, schema=ErrorSchema, description="관리자 권한 없음")
@blp.alt_response(404, schema=ErrorSchema, description="사용자 없음")
def update_user_role(user_id: int):
    admin_err = require_admin()
    if admin_err:
        return admin_err, 403

    user = User.query.get(user_id)
    if not user:
        return error_response(
            status=404,
            code="USER_NOT_FOUND",
            message="User not found",
        ), 404

    data = request.get_json() or {}
    new_role = data.get("role")

    if new_role not in ("USER", "ADMIN"):
        return error_response(
            status=400,
            code="VALIDATION_FAILED",
            message="role must be 'USER' or 'ADMIN'",
        ), 400

    user.role = new_role
    db.session.commit()

    return jsonify(
        {
            "userId": user.user_id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "isActive": user.is_active,
        }
    )


@blp.route("/<int:user_id>/deactivate", methods=["PATCH"])
@jwt_required()
@blp.alt_response(401, schema=ErrorSchema, description="인증 실패")
@blp.alt_response(403, schema=ErrorSchema, description="관리자 권한 없음")
@blp.alt_response(404, schema=ErrorSchema, description="사용자 없음")
def deactivate_user(user_id: int):
    admin_err = require_admin()
    if admin_err:
        return admin_err, 403

    user = User.query.get(user_id)
    if not user:
        return error_response(
            status=404,
            code="USER_NOT_FOUND",
            message="User not found",
        ), 404

    user.is_active = False
    db.session.commit()

    return jsonify(
        {
            "userId": user.user_id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "isActive": user.is_active,
        }
    )
