from enum import StrEnum
from urllib.parse import urlsplit

from clarity_core.net.guard import AddressGuard, UnsafeTargetError

READ_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
NETWORK_SCHEMES = frozenset({"http", "https", "ws", "wss"})


class Verdict(StrEnum):
    ALLOW = "allow"
    BLOCK_MUTATION = "block_mutation"
    BLOCK_ADDRESS = "block_address"


class RequestPolicy:
    def __init__(self, guard: AddressGuard, *, allow_mutations: bool = False) -> None:
        self.guard = guard
        self.allow_mutations = allow_mutations
        self._hosts: dict[str, bool] = {}

    async def evaluate(self, method: str, url: str) -> Verdict:
        parts = urlsplit(url)
        if parts.scheme not in NETWORK_SCHEMES:
            return Verdict.ALLOW
        if not await self._host_allowed(parts.hostname or ""):
            return Verdict.BLOCK_ADDRESS
        if method.upper() not in READ_METHODS and not self.allow_mutations:
            return Verdict.BLOCK_MUTATION
        return Verdict.ALLOW

    async def _host_allowed(self, host: str) -> bool:
        if host not in self._hosts:
            try:
                await self.guard.check_url(f"http://{_bracket(host)}/")
                self._hosts[host] = True
            except UnsafeTargetError:
                self._hosts[host] = False
        return self._hosts[host]


def _bracket(host: str) -> str:
    return f"[{host}]" if ":" in host else host
