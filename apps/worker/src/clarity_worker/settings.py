import ipaddress
from functools import cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from clarity_core.net.guard import AddressGuard, IPNetwork


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CLARITY_", env_file=".env", extra="ignore")

    database_url: str
    artifact_dir: Path = Path("var/artifacts")
    egress_proxy: str | None = None
    allowed_networks: list[str] = Field(default_factory=list)
    concurrency: int = Field(default=1, ge=1, le=8)

    def guard(self) -> AddressGuard:
        networks: list[IPNetwork] = [ipaddress.ip_network(net) for net in self.allowed_networks]
        return AddressGuard(allow=networks)


@cache
def get_settings() -> WorkerSettings:
    return WorkerSettings()
