import time

from clarity_api.security import (
    SessionSigner,
    hash_extension_key,
    hash_password,
    new_extension_key,
    verify_password,
)


def test_password_hashing() -> None:
    hashed = hash_password("correct horse")
    assert verify_password(hashed, "correct horse")
    assert not verify_password(hashed, "wrong")
    assert not verify_password("not-a-hash", "correct horse")


def test_session_tokens_roundtrip_and_reject_tampering() -> None:
    signer = SessionSigner("s3cret", max_age=60)
    token = signer.issue("admin")
    assert signer.read(token) == "admin"
    assert signer.read(token + "x") is None
    assert SessionSigner("other", max_age=60).read(token) is None


def test_session_tokens_expire() -> None:
    signer = SessionSigner("s3cret", max_age=1)
    token = signer.issue("admin")
    time.sleep(2.1)
    assert signer.read(token) is None


def test_extension_keys_are_unique_and_hashed() -> None:
    first, second = new_extension_key(), new_extension_key()
    assert first != second
    assert first.startswith("cc_")
    assert hash_extension_key(first) == hash_extension_key(first)
    assert len(hash_extension_key(first)) == 64
