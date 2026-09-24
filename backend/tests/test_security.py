from app.core.security import create_access_token, decode_token, hash_password, verify_password


def test_password_hashing_round_trip() -> None:
    password = "correct horse battery staple"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong password", hashed)


def test_access_token_contains_expected_subject_and_type() -> None:
    token = create_access_token("user-id")
    payload = decode_token(token)

    assert payload["sub"] == "user-id"
    assert payload["type"] == "access"
