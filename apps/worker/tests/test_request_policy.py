import pytest

from clarity_core.net.guard import AddressGuard
from clarity_worker.policy import RequestPolicy, Verdict


async def public(host: str) -> list[str]:
    return {"theqiyas.cc": ["93.184.215.14"], "intranet.test": ["10.0.0.2"]}[host]


@pytest.fixture
def policy() -> RequestPolicy:
    return RequestPolicy(AddressGuard(resolve=public))


async def test_read_requests_to_public_hosts_pass(policy: RequestPolicy) -> None:
    assert await policy.evaluate("GET", "https://theqiyas.cc/a.css") is Verdict.ALLOW


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
async def test_mutating_requests_are_blocked_by_default(
    policy: RequestPolicy, method: str
) -> None:
    assert await policy.evaluate(method, "https://theqiyas.cc/api") is Verdict.BLOCK_MUTATION


async def test_mutations_can_be_permitted(policy: RequestPolicy) -> None:
    policy.allow_mutations = True
    assert await policy.evaluate("POST", "https://theqiyas.cc/api") is Verdict.ALLOW


async def test_private_destination_is_blocked(policy: RequestPolicy) -> None:
    assert await policy.evaluate("GET", "https://intranet.test/") is Verdict.BLOCK_ADDRESS


async def test_non_network_schemes_pass(policy: RequestPolicy) -> None:
    assert await policy.evaluate("GET", "data:image/png;base64,AAAA") is Verdict.ALLOW
    assert await policy.evaluate("GET", "blob:https://theqiyas.cc/1") is Verdict.ALLOW


async def test_resolution_is_cached_per_host() -> None:
    calls: list[str] = []

    async def counting(host: str) -> list[str]:
        calls.append(host)
        return ["93.184.215.14"]

    policy = RequestPolicy(AddressGuard(resolve=counting))
    for path in ("a", "b", "c"):
        await policy.evaluate("GET", f"https://theqiyas.cc/{path}")
    assert calls == ["theqiyas.cc"]
