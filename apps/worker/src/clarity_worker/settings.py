import ipaddress
from functools import cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from clarity_core.net.guard import AddressGuard, IPNetwork


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CLARITY_", env_file=".env", extra="ignore")

    database_url: str
    artifact_dir: Path = Path("var/artifacts")
    model_dir: Path = Path("models")
    egress_proxy: str | None = None
    allowed_networks: list[str] = Field(default_factory=list)
    concurrency: int = Field(default=1, ge=1, le=8)
    ai_provider: Literal["anthropic", "openai", "none"] = "none"
    ai_model: str | None = None
    ai_base_url: str | None = None
    ai_api_key: SecretStr | None = None
    credentials_key: SecretStr | None = None

    def guard(self) -> AddressGuard:
        networks: list[IPNetwork] = [ipaddress.ip_network(net) for net in self.allowed_networks]
        return AddressGuard(allow=networks, allow_unresolved=self.egress_proxy is not None)


@cache
def get_settings() -> WorkerSettings:
    return WorkerSettings()
