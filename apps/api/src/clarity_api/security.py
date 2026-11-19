import base64
import hashlib
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from cryptography.fernet import Fernet, InvalidToken
from itsdangerous import BadSignature, URLSafeTimedSerializer

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


class SessionSigner:
    def __init__(self, secret: str, max_age: int) -> None:
        self._serializer = URLSafeTimedSerializer(secret, salt="clarity.session")
        self.max_age = max_age

    def issue(self, username: str) -> str:
        return self._serializer.dumps({"sub": username})

    def read(self, token: str) -> str | None:
        try:
            payload = self._serializer.loads(token, max_age=self.max_age)
        except BadSignature:
            return None
        subject = payload.get("sub") if isinstance(payload, dict) else None
        return subject if isinstance(subject, str) else None


class SecretBox:
    def __init__(self, key: str) -> None:
        digest = hashlib.sha256(key.encode()).digest()
        self._fernet = Fernet(base64.urlsafe_b64encode(digest))

    def seal(self, plaintext: bytes) -> bytes:
        return self._fernet.encrypt(plaintext)

    def open(self, token: bytes) -> bytes:
        try:
            return self._fernet.decrypt(token)
        except InvalidToken as exc:
            raise ValueError("cannot decrypt sealed value") from exc


def new_extension_key() -> str:
    return f"cc_{secrets.token_urlsafe(24)}"


def hash_extension_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()
