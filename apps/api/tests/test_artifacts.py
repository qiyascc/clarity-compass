from httpx import AsyncClient

from clarity_api.settings import Settings


async def test_serves_stored_artifacts(client: AsyncClient, settings: Settings) -> None:
    target = settings.artifact_dir / "run" / "desktop" / "section-00.png"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"\x89PNG")
    response = await client.get("/api/artifacts/run/desktop/section-00.png")
    assert response.status_code == 200
    assert response.content == b"\x89PNG"
    assert response.headers["content-type"] == "image/png"


async def test_requires_login(anonymous: AsyncClient) -> None:
    assert (await anonymous.get("/api/artifacts/run/x.png")).status_code == 401


async def test_traversal_is_refused(client: AsyncClient, settings: Settings) -> None:
    settings.artifact_dir.mkdir(parents=True)
    (settings.artifact_dir.parent / "secret.txt").write_text("nope")
    for path in ("../secret.txt", "..%2Fsecret.txt", "%2e%2e/secret.txt"):
        assert (await client.get(f"/api/artifacts/{path}")).status_code == 404
