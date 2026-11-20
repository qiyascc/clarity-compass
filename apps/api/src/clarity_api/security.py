import hashlib
import secrets
import time
from collections import defaultdict, deque

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
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


def new_extension_key() -> str:
    return f"cc_{secrets.token_urlsafe(24)}"


def hash_extension_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


class LoginThrottle:
    def __init__(self, max_failures: int = 5, window: float = 60.0) -> None:
        self.max_failures = max_failures
        self.window = window
        self._failures: defaultdict[str, deque[float]] = defaultdict(deque)

    def blocked(self, client: str) -> bool:
        failures = self._failures[client]
        cutoff = time.monotonic() - self.window
        while failures and failures[0] < cutoff:
            failures.popleft()
        return len(failures) >= self.max_failures

    def failed(self, client: str) -> None:
        self._failures[client].append(time.monotonic())

    def reset(self, client: str) -> None:
        self._failures.pop(client, None)
