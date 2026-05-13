import uuid

from app.services.auth import create_access_token, decode_access_token, hash_password, verify_password


def test_hash_and_verify_password() -> None:
    hashed = hash_password("secret123")
    assert hashed != "secret123"
    assert verify_password("secret123", hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_create_and_decode_access_token() -> None:
    user_id = uuid.uuid4()
    token = create_access_token(user_id)
    assert isinstance(token, str)
    assert len(token) > 0

    decoded = decode_access_token(token)
    assert decoded == user_id


def test_decode_invalid_token() -> None:
    result = decode_access_token("invalid.token.here")
    assert result is None


def test_decode_empty_token() -> None:
    result = decode_access_token("")
    assert result is None


def test_hash_password_different_each_time() -> None:
    h1 = hash_password("samepassword")
    h2 = hash_password("samepassword")
    assert h1 != h2
    assert verify_password("samepassword", h1) is True
    assert verify_password("samepassword", h2) is True
