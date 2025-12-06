# src/api/reviews.py

from flask import request, jsonify
from flask_smorest import Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import and_

from src.app.extensions import db
from src.app.models import Review, Book, User
from src.app.common.errors import error_response
from src.app.schemas.common import ErrorSchema

blp = Blueprint(
    "Reviews",
    __name__,
    url_prefix="",
    description="Book Review APIs",
)


# -------------------------------------------------------------
# 공통 유틸
# -------------------------------------------------------------
def parse_pagination():
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


def get_current_user():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user:
        return None, error_response(
            status=404,
            code="USER_NOT_FOUND",
            message="User not found",
        )

    if not user.is_active:
        return None, error_response(
            status=403,
            code="FORBIDDEN",
            message="User is deactivated",
        )

    return user, None


# -------------------------------------------------------------
# 1) 특정 도서 리뷰 목록 / 생성
# GET /books/{book_id}/reviews
# POST /books/{book_id}/reviews
# -------------------------------------------------------------
@blp.route("/books/<int:book_id>/reviews", methods=["GET"])
@blp.alt_response(404, schema=ErrorSchema)
def list_book_reviews(book_id):
    page, size, err = parse_pagination()
    if err:
        return err, 400

    book = Book.query.get(book_id)
    if not book:
        return error_response(
            status=404,
            code="BOOK_NOT_FOUND",
            message="Book not found",
        ), 404

    query = Review.query.filter(Review.book_id == book_id)

    min_rating = request.args.get("minRating")
    max_rating = request.args.get("maxRating")
    try:
        if min_rating:
            query = query.filter(Review.rating >= float(min_rating))
        if max_rating:
            query = query.filter(Review.rating <= float(max_rating))
    except ValueError:
        return error_response(
            status=400,
            code="INVALID_QUERY_PARAM",
            message="rating must be number",
        ), 400

    pagination = query.order_by(Review.created_at.desc()).paginate(
        page=page, per_page=size, error_out=False
    )

    content = [{
        "reviewId": r.review_id,
        "userId": r.user_id,
        "rating": float(r.rating),
        "content": r.content,
        "createdAt": r.created_at.isoformat(),
    } for r in pagination.items]

    return jsonify({
        "bookId": book_id,
        "content": content,
        "page": page,
        "size": size,
        "totalElements": pagination.total,
        "totalPages": pagination.pages,
    })


@blp.route("/books/<int:book_id>/reviews", methods=["POST"])
@jwt_required()
@blp.alt_response(400, schema=ErrorSchema)
@blp.alt_response(409, schema=ErrorSchema)
def create_review(book_id):
    user, err = get_current_user()
    if err:
        return err, 403

    book = Book.query.get(book_id)
    if not book:
        return error_response(
            status=404,
            code="BOOK_NOT_FOUND",
            message="Book not found",
        ), 404

    data = request.get_json() or {}
    rating = data.get("rating")
    content = (data.get("content") or "").strip()

    if rating is None:
        return error_response(
            status=400,
            code="VALIDATION_FAILED",
            message="rating is required",
        ), 400

    try:
        rating = float(rating)
    except ValueError:
        return error_response(
            status=400,
            code="VALIDATION_FAILED",
            message="rating must be number",
        ), 400

    if not (1 <= rating <= 5):
        return error_response(
            status=400,
            code="VALIDATION_FAILED",
            message="rating must be 1~5",
        ), 400

    if Review.query.filter(
        and_(Review.book_id == book_id, Review.user_id == user.user_id)
    ).first():
        return error_response(
            status=409,
            code="DUPLICATE_REVIEW",
            message="You already reviewed this book",
        ), 409

    review = Review(
        book_id=book_id,
        user_id=user.user_id,
        rating=rating,
        content=content,
    )
    db.session.add(review)
    db.session.commit()

    return jsonify({
        "reviewId": review.review_id,
        "rating": float(review.rating),
        "content": review.content,
    }), 201


# -------------------------------------------------------------
# 2) 단일 리뷰 조회 / 수정 / 삭제
# GET /reviews/{id}
# PATCH /reviews/{id}
# DELETE /reviews/{id}
# -------------------------------------------------------------
@blp.route("/reviews/<int:review_id>", methods=["GET"])
@blp.alt_response(404, schema=ErrorSchema)
def get_review(review_id):
    review = Review.query.get(review_id)
    if not review:
        return error_response(
            status=404,
            code="REVIEW_NOT_FOUND",
            message="Review not found",
        ), 404

    return jsonify({
        "reviewId": review.review_id,
        "userId": review.user_id,
        "bookId": review.book_id,
        "rating": float(review.rating),
        "content": review.content,
        "createdAt": review.created_at.isoformat(),
    })


@blp.route("/reviews/<int:review_id>", methods=["PATCH"])
@jwt_required()
def update_review(review_id):
    user, err = get_current_user()
    if err:
        return err, 403

    review = Review.query.get(review_id)
    if not review:
        return error_response(
            status=404,
            code="REVIEW_NOT_FOUND",
            message="Review not found",
        ), 404

    claims = get_jwt()
    if review.user_id != user.user_id and claims.get("role") != "ADMIN":
        return error_response(
            status=403,
            code="FORBIDDEN",
            message="No permission",
        ), 403

    data = request.get_json() or {}

    if "rating" in data:
        try:
            rating = float(data["rating"])
            if not 1 <= rating <= 5:
                raise ValueError
            review.rating = rating
        except ValueError:
            return error_response(
                status=400,
                code="VALIDATION_FAILED",
                message="rating must be 1~5",
            ), 400

    if "content" in data:
        review.content = data["content"].strip()

    db.session.commit()

    return jsonify({
        "reviewId": review.review_id,
        "rating": float(review.rating),
        "content": review.content,
    })


@blp.route("/reviews/<int:review_id>", methods=["DELETE"])
@jwt_required()
def delete_review(review_id):
    user, err = get_current_user()
    if err:
        return err, 403

    review = Review.query.get(review_id)
    if not review:
        return error_response(
            status=404,
            code="REVIEW_NOT_FOUND",
            message="Review not found",
        ), 404

    claims = get_jwt()
    if review.user_id != user.user_id and claims.get("role") != "ADMIN":
        return error_response(
            status=403,
            code="FORBIDDEN",
            message="No permission",
        ), 403

    db.session.delete(review)
    db.session.commit()
    return "", 204


# -------------------------------------------------------------
# 3) 리뷰 검색 (전체)
# GET /reviews?userId=&bookId=&minRating=&maxRating=
# -------------------------------------------------------------
@blp.route("/reviews", methods=["GET"])
def list_reviews():
    page, size, err = parse_pagination()
    if err:
        return err, 400

    query = Review.query

    if "userId" in request.args:
        query = query.filter(Review.user_id == int(request.args["userId"]))
    if "bookId" in request.args:
        query = query.filter(Review.book_id == int(request.args["bookId"]))

    pagination = query.order_by(Review.created_at.desc()).paginate(
        page=page, per_page=size, error_out=False
    )

    return jsonify({
        "content": [{
            "reviewId": r.review_id,
            "bookId": r.book_id,
            "userId": r.user_id,
            "rating": float(r.rating),
        } for r in pagination.items],
        "page": page,
        "size": size,
        "totalElements": pagination.total,
        "totalPages": pagination.pages,
    })
