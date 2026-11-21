import pytest
from pydantic import SecretStr

from clarity_api.settings import Settings

REQUIRED = {
    "database_url": "postgresql+asyncpg://unused",
    "secret_key": SecretStr("s"),
    "credentials_key": SecretStr("c"),
    "admin_username": "admin",
    "admin_password_hash": SecretStr("h"),
    "_env_file": None,
}


def test_users_are_read_from_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLARITY_USERS", '{"editor": "$argon2id$v=19$m=1,t=1,p=1$abc$def"}')
    settings = Settings(**REQUIRED)
    assert settings.password_hash("editor") == "$argon2id$v=19$m=1,t=1,p=1$abc$def"
    assert settings.password_hash("admin") == "h"
    assert settings.password_hash("stranger") is None


def test_an_empty_users_variable_means_no_extra_users(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLARITY_USERS", "")
    assert Settings(**REQUIRED).users == {}
