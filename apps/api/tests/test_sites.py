import uuid

from fastapi import FastAPI
from httpx import AsyncClient

from clarity_persistence.models import Site
from clarity_persistence.secrets import SecretBox

QIYAS: dict[str, object] = {"name": "Qiyas", "profile": {"start_url": "theqiyas.cc"}}


async def create(client: AsyncClient, payload: dict[str, object] = QIYAS) -> dict[str, object]:
    response = await client.post("/api/sites", json=payload)
    assert response.status_code == 201, response.text
    body: dict[str, object] = response.json()
    return body


async def test_sites_require_login(anonymous: AsyncClient) -> None:
    assert (await anonymous.get("/api/sites")).status_code == 401
    assert (await anonymous.post("/api/sites", json=QIYAS)).status_code == 401


async def test_create_and_list(client: AsyncClient) -> None:
    site = await create(client)
    assert site["start_url"] == "https://theqiyas.cc/"
    assert site["has_credentials"] is False
    listed = (await client.get("/api/sites")).json()
    assert [item["id"] for item in listed] == [site["id"]]


async def test_invalid_profile_is_rejected(client: AsyncClient) -> None:
    payload = {"name": "Bad", "profile": {"start_url": "ftp://theqiyas.cc"}}
    assert (await client.post("/api/sites", json=payload)).status_code == 422


async def test_update_profile(client: AsyncClient) -> None:
    site = await create(client)
    response = await client.patch(
        f"/api/sites/{site['id']}",
        json={"profile": {"start_url": "qiyas.cc", "scope": "single", "language": "tr"}},
    )
    body = response.json()
    assert body["start_url"] == "https://qiyas.cc/"
    assert body["profile"]["language"] == "tr"
    assert body["profile"]["limits"]["max_pages"] == 1


async def test_unknown_site(client: AsyncClient) -> None:
    assert (await client.get(f"/api/sites/{uuid.uuid4()}")).status_code == 404


async def test_delete(client: AsyncClient) -> None:
    site = await create(client)
    assert (await client.delete(f"/api/sites/{site['id']}")).status_code == 204
    assert (await client.get(f"/api/sites/{site['id']}")).status_code == 404


async def test_credentials_are_sealed_and_never_returned(client: AsyncClient, app: FastAPI) -> None:
    site = await create(client)
    response = await client.put(
        f"/api/sites/{site['id']}/credentials",
        json={"login_url": "https://theqiyas.cc/login", "username": "me", "password": "hunter2"},
    )
    assert response.status_code == 204
    body = (await client.get(f"/api/sites/{site['id']}")).json()
    assert body["has_credentials"] is True
    assert "hunter2" not in str(body)

    async with app.state.sessions() as db:
        stored = await db.get(Site, uuid.UUID(str(site["id"])))
        assert stored is not None
        assert stored.credentials is not None
        assert b"hunter2" not in stored.credentials
        box: SecretBox = app.state.secret_box
        assert b"hunter2" in box.open(stored.credentials)

    await client.delete(f"/api/sites/{site['id']}/credentials")
    assert (await client.get(f"/api/sites/{site['id']}")).json()["has_credentials"] is False


async def test_extension_key_is_shown_once_and_rotates(client: AsyncClient) -> None:
    site = await create(client)
    first = await client.post(f"/api/sites/{site['id']}/extension-key")
    assert first.status_code == 201
    assert first.headers["cache-control"] == "no-store"
    second = await client.post(f"/api/sites/{site['id']}/extension-key")
    assert first.json()["key"] != second.json()["key"]
    body = (await client.get(f"/api/sites/{site['id']}")).json()
    assert body["has_extension_key"] is True
    assert first.json()["key"] not in str(body)
