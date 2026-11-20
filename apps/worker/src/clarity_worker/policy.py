from enum import StrEnum
from urllib.parse import urlsplit

from clarity_core.net.guard import AddressGuard, UnsafeTargetError
from clarity_core.net.urls import same_site

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
        self._mutations_for: str | None = None
        self._hosts: dict[str, bool] = {}

    def allow_mutations_to(self, url: str | None) -> None:
        """Lets writes through to one site only, e.g. while submitting a login form."""
        self._mutations_for = url

    async def evaluate(self, method: str, url: str) -> Verdict:
        parts = urlsplit(url)
        if parts.scheme not in NETWORK_SCHEMES:
            return Verdict.ALLOW
        if not await self._host_allowed(parts.hostname or ""):
            return Verdict.BLOCK_ADDRESS
        if method.upper() not in READ_METHODS and not self._mutation_allowed(url):
            return Verdict.BLOCK_MUTATION
        return Verdict.ALLOW

    def _mutation_allowed(self, url: str) -> bool:
        if self.allow_mutations:
            return True
        return self._mutations_for is not None and same_site(url, self._mutations_for)

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
