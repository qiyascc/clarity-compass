import ipaddress

import pytest

from clarity_core.net.guard import AddressGuard, Resolver, UnsafeTargetError


def resolver(table: dict[str, list[str]]) -> Resolver:
    async def resolve(host: str) -> list[str]:
        return table[host]

    return resolve


@pytest.mark.parametrize(
    "address",
    [
        "127.0.0.1",
        "10.1.2.3",
        "172.16.0.9",
        "192.168.1.1",
        "169.254.169.254",
        "100.64.0.1",
        "0.0.0.0",
        "224.0.0.1",
        "::1",
        "fd00::1",
        "fe80::1",
        "::ffff:127.0.0.1",
        "64:ff9b::7f00:1",
    ],
)
def test_non_public_addresses_are_blocked(address: str) -> None:
    assert not AddressGuard().is_allowed(ipaddress.ip_address(address))


@pytest.mark.parametrize("address", ["93.184.215.14", "2606:4700::6810:84e5"])
def test_public_addresses_are_allowed(address: str) -> None:
    assert AddressGuard().is_allowed(ipaddress.ip_address(address))


async def test_check_url_rejects_when_any_record_is_private() -> None:
    guard = AddressGuard(resolve=resolver({"mixed.test": ["93.184.215.14", "10.0.0.5"]}))
    with pytest.raises(UnsafeTargetError, match=r"10\.0\.0\.5"):
        await guard.check_url("https://mixed.test/")


async def test_check_url_rejects_literal_private_ip_without_resolving() -> None:
    guard = AddressGuard(resolve=resolver({}))
    with pytest.raises(UnsafeTargetError):
        await guard.check_url("http://[::1]:8000/")


async def test_check_url_returns_resolved_addresses() -> None:
    guard = AddressGuard(resolve=resolver({"theqiyas.cc": ["93.184.215.14"]}))
    addresses = await guard.check_url("https://theqiyas.cc/")
    assert addresses == [ipaddress.ip_address("93.184.215.14")]


async def test_unresolvable_host_is_rejected() -> None:
    async def fail(host: str) -> list[str]:
        raise OSError("nxdomain")

    with pytest.raises(UnsafeTargetError, match="resolve"):
        await AddressGuard(resolve=fail).check_url("https://nope.invalid/")


async def test_allowlisted_network_is_permitted() -> None:
    guard = AddressGuard(
        resolve=resolver({"fixture.local": ["127.0.0.1"]}),
        allow=[ipaddress.ip_network("127.0.0.0/8")],
    )
    assert await guard.check_url("http://fixture.local/")
