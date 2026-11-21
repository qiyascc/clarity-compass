from functools import cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CLARITY_", env_file=".env", extra="ignore", env_ignore_empty=True
    )

    database_url: str
    secret_key: SecretStr
    credentials_key: SecretStr
    admin_username: str = "admin"
    admin_password_hash: SecretStr
    users: dict[str, SecretStr] = Field(default_factory=dict)
    artifact_dir: Path = Path("var/artifacts")
    session_max_age: int = Field(default=7 * 24 * 3600, ge=300)
    secure_cookies: bool = True
    allowed_origins: list[str] = Field(default_factory=list)

    def password_hash(self, username: str) -> str | None:
        if username == self.admin_username:
            return self.admin_password_hash.get_secret_value()
        stored = self.users.get(username)
        return stored.get_secret_value() if stored else None


@cache
def get_settings() -> Settings:
    return Settings()
