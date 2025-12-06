# src/app/common/errors.py

from datetime import datetime, timezone
from flask import jsonify, request


def error_response(status: int, code: str, message: str, details: dict | None = None, path: str | None = None):
    """
    과제에서 요구한 표준 에러 포맷을 생성하는 헬퍼 함수.

    사용 예시:
        return error_response(
            status=400,
            code="VALIDATION_FAILED",
            message="email is required",
            details={"email": "missing"},
        ), 400
    """
    # 요청 경로 자동 설정 (필요하면 덮어쓸 수 있게 path 파라미터 허용)
    if path is None:
        try:
            path = request.path
        except RuntimeError:
            # request context가 없는 경우 대비
            path = None

    body = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "path": path,
        "status": status,
        "code": code,
        "message": message,
    }

    if details is not None:
        body["details"] = details

    # 여기서는 Response 객체만 반환하고,
    # 실제 view 함수에서 ", status"를 붙여서 HTTP 코드 설정
    return jsonify(body)
