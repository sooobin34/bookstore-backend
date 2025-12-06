from werkzeug.security import generate_password_hash, check_password_hash


def hash_password(plain_password: str) -> str:
    """
    평문 비밀번호를 안전하게 해시
    """
    return generate_password_hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    평문과 해시를 비교
    """
    return check_password_hash(hashed_password, plain_password)
