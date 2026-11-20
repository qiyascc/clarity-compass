from functools import cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CLARITY_", env_file=".env", extra="ignore")

    database_url: str
    secret_key: SecretStr
    credentials_key: SecretStr
    admin_username: str = "admin"
    admin_password_hash: SecretStr
    artifact_dir: Path = Path("var/artifacts")
    session_max_age: int = Field(default=7 * 24 * 3600, ge=300)
    secure_cookies: bool = True
    allowed_origins: list[str] = Field(default_factory=list)


@cache
def get_settings() -> Settings:
    return Settings()
