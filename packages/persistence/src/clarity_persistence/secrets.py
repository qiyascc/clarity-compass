import base64
import hashlib
import json
from dataclasses import asdict, dataclass

from cryptography.fernet import Fernet, InvalidToken


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


@dataclass(frozen=True)
class SiteLogin:
    login_url: str
    username: str
    password: str
    username_selector: str | None = None
    password_selector: str | None = None
    submit_selector: str | None = None

    def seal(self, box: SecretBox) -> bytes:
        return box.seal(json.dumps(asdict(self)).encode())

    @classmethod
    def open(cls, box: SecretBox, sealed: bytes) -> "SiteLogin":
        data = json.loads(box.open(sealed))
        return cls(**{name: data.get(name) for name in cls.__dataclass_fields__})

    def __repr__(self) -> str:
        return f"SiteLogin(login_url={self.login_url!r}, username={self.username!r}, password=***)"
