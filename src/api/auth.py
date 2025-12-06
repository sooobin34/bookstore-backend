# src/api/auth.py

from flask import request, jsonify
from flask_smorest import Blueprint
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
)
from src.app.extensions import db
from src.app.models import User
from src.app.common.errors import error_response
from src.app.security import hash_password, verify_password
from src.app.schemas.user import UserSignupSchema, UserLoginSchema
from src.app.schemas.common import ErrorSchema


blp = Blueprint(
    "Auth",
    __name__,
    url_prefix="/auth",
    description="Authentication / JWT Login APIs",
)


# ---------------------------------------------------------
# POST /auth/signup — 회원가입
# ---------------------------------------------------------
@blp.route("/signup", methods=["POST"])
@blp.arguments(UserSignupSchema)
@blp.response(201)
@blp.alt_response(400, schema=ErrorSchema, description="필수값 누락 / 형식 오류")
@blp.alt_response(409, schema=ErrorSchema, description="이메일 중복")
@blp.alt_response(500, schema=ErrorSchema, description="서버 오류")
def signup(data):
    """
    회원가입 — ROLE_USER 기본값
    """
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    # 필드 검증
    if not all([name, email, password]):
        return error_response(
            status=400,
            code="VALIDATION_FAILED",
            message="name, email, password are required",
        ), 400

    # 이메일 중복 방지
    if User.query.filter_by(email=email).first():
        return error_response(
            status=409,
            code="DUPLICATE_RESOURCE",
            message="Email already registered",
        ), 409

    user = User(
        name=name,
        email=email,
        password=hash_password(password),
        role="USER",
    )
    db.session.add(user)
    db.session.commit()

    return jsonify(
        {
            "userId": user.user_id,
            "email": user.email,
            "name": user.name,
        }
    ), 201


# ---------------------------------------------------------
# POST /auth/login — 로그인 & JWT 발급
# ---------------------------------------------------------
@blp.route("/login", methods=["POST"])
@blp.arguments(UserLoginSchema)
@blp.response(200)
@blp.alt_response(400, schema=ErrorSchema, description="입력 값 누락")
@blp.alt_response(401, schema=ErrorSchema, description="이메일/비밀번호 불일치")
@blp.alt_response(500, schema=ErrorSchema, description="서버 오류")
def login(data):
    """
    로그인 — AccessToken + RefreshToken 발급
    """
    email = data.get("email")
    password = data.get("password")

    if not all([email, password]):
        return error_response(
            status=400,
            code="VALIDATION_FAILED",
            message="email and password are required",
        ), 400

    user = User.query.filter_by(email=email).first()

    if not user or not verify_password(password, user.password):
        return error_response(
            status=401,
            code="UNAUTHORIZED",
            message="Invalid email or password",
        ), 401

    # JWT Claims
    claims = {"email": user.email, "role": user.role}

    access_token = create_access_token(identity=str(user.user_id), additional_claims=claims)
    refresh_token = create_refresh_token(identity=str(user.user_id), additional_claims=claims)

    return jsonify(
        {
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "tokenType": "Bearer",
        }
    ), 200


# ---------------------------------------------------------
# POST /auth/refresh — RefreshToken으로 AccessToken 재발급
# ---------------------------------------------------------
@blp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
@blp.response(200)
@blp.alt_response(401, schema=ErrorSchema, description="RefreshToken 누락 또는 유효하지 않음")
@blp.alt_response(404, schema=ErrorSchema, description="User not found")
@blp.alt_response(500, schema=ErrorSchema, description="서버 오류")
def refresh():
    """
    Refresh 토큰으로 Access Token 재발급
    """
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))

    if not user:
        return error_response(
            status=404,
            code="USER_NOT_FOUND",
            message="User not found",
        ), 404

    claims = {"email": user.email, "role": user.role}

    new_access = create_access_token(identity=str(user.user_id), additional_claims=claims)

    return jsonify(
        {
            "accessToken": new_access,
            "tokenType": "Bearer",
        }
    ), 200
