from flask import jsonify


def make_response(status: str, http_status: int, data=None, message: str | None = None):
    """
    공통 성공 응답 포맷 헬퍼.

    예:
      return make_response("success", 200, data={"id": 1}, message="OK")
    """
    body = {
        "status": status,
        "data": data,
        "message": message,
    }
    return jsonify(body), http_status
