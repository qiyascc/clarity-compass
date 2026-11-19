import asyncio
import ipaddress
import socket
from collections.abc import Awaitable, Callable, Iterable
from urllib.parse import urlsplit

IPAddress = ipaddress.IPv4Address | ipaddress.IPv6Address
IPNetwork = ipaddress.IPv4Network | ipaddress.IPv6Network
Resolver = Callable[[str], Awaitable[list[str]]]

NAT64_PREFIX = ipaddress.ip_network("64:ff9b::/96")


class UnsafeTargetError(Exception):
    pass


async def system_resolve(host: str) -> list[str]:
    loop = asyncio.get_running_loop()
    infos = await loop.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    return list(dict.fromkeys(str(info[4][0]) for info in infos))


class AddressGuard:
    def __init__(
        self,
        resolve: Resolver = system_resolve,
        allow: Iterable[IPNetwork] = (),
    ) -> None:
        self._resolve = resolve
        self._allow = tuple(allow)

    def is_allowed(self, address: IPAddress) -> bool:
        if any(address in network for network in self._allow):
            return True
        return all(_is_public(candidate) for candidate in _embedded(address))

    async def check_url(self, url: str) -> list[IPAddress]:
        host = urlsplit(url).hostname
        if not host:
            raise UnsafeTargetError(f"no host in {url!r}")
        addresses = await self._addresses(host)
        blocked = [str(address) for address in addresses if not self.is_allowed(address)]
        if blocked:
            raise UnsafeTargetError(f"{host} points to non-public address {', '.join(blocked)}")
        return addresses

    async def _addresses(self, host: str) -> list[IPAddress]:
        try:
            return [ipaddress.ip_address(host)]
        except ValueError:
            pass
        try:
            records = await self._resolve(host)
        except OSError as exc:
            raise UnsafeTargetError(f"cannot resolve {host}") from exc
        if not records:
            raise UnsafeTargetError(f"cannot resolve {host}")
        return [ipaddress.ip_address(record.split("%", 1)[0]) for record in records]


def _embedded(address: IPAddress) -> list[IPAddress]:
    found: list[IPAddress] = [address]
    if isinstance(address, ipaddress.IPv6Address):
        if address.ipv4_mapped:
            found.append(address.ipv4_mapped)
        if address.sixtofour:
            found.append(address.sixtofour)
        if address.teredo:
            found.extend(address.teredo)
        if address in NAT64_PREFIX:
            found.append(ipaddress.IPv4Address(int(address) & 0xFFFFFFFF))
    return found


def _is_public(address: IPAddress) -> bool:
    return address.is_global and not address.is_multicast and not address.is_reserved
