from fastapi import FastAPI
from httpx import AsyncClient


async def test_health(anonymous: AsyncClient) -> None:
    response = await anonymous.get("/api/health")
    assert response.json() == {"status": "ok"}


async def test_login_sets_an_http_only_cookie(anonymous: AsyncClient, password: str) -> None:
    response = await anonymous.post(
        "/api/auth/login", json={"username": "admin", "password": password}
    )
    assert response.status_code == 204
    assert "httponly" in response.headers["set-cookie"].lower()
    me = await anonymous.get("/api/auth/me")
    assert me.json() == {"username": "admin"}


async def test_wrong_password_is_rejected(anonymous: AsyncClient) -> None:
    response = await anonymous.post("/api/auth/login", json={"username": "admin", "password": "x"})
    assert response.status_code == 401
    assert (await anonymous.get("/api/auth/me")).status_code == 401


async def test_repeated_failures_are_throttled(anonymous: AsyncClient, password: str) -> None:
    for _ in range(5):
        await anonymous.post("/api/auth/login", json={"username": "admin", "password": "x"})
    response = await anonymous.post(
        "/api/auth/login", json={"username": "admin", "password": password}
    )
    assert response.status_code == 429


async def test_logout_clears_the_session(client: AsyncClient) -> None:
    await client.post("/api/auth/logout")
    assert (await client.get("/api/auth/me")).status_code == 401


async def test_forged_cookie_is_ignored(anonymous: AsyncClient) -> None:
    anonymous.cookies.set("cc_session", "eyJzdWIiOiJhZG1pbiJ9.forged.sig")
    assert (await anonymous.get("/api/auth/me")).status_code == 401


async def test_additional_users_can_sign_in(anonymous: AsyncClient, password: str) -> None:
    response = await anonymous.post(
        "/api/auth/login", json={"username": "editor", "password": password}
    )
    assert response.status_code == 204
    assert (await anonymous.get("/api/auth/me")).json() == {"username": "editor"}


async def test_unknown_users_are_rejected(anonymous: AsyncClient, password: str) -> None:
    response = await anonymous.post(
        "/api/auth/login", json={"username": "stranger", "password": password}
    )
    assert response.status_code == 401


async def test_removing_a_user_ends_their_session(
    anonymous: AsyncClient, app: FastAPI, password: str
) -> None:
    await anonymous.post("/api/auth/login", json={"username": "editor", "password": password})
    app.state.settings.users.pop("editor")
    assert (await anonymous.get("/api/auth/me")).status_code == 401
