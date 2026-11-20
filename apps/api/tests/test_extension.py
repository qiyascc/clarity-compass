import uuid
from datetime import UTC, datetime

from fastapi import FastAPI
from httpx import AsyncClient

from clarity_api.settings import Settings
from clarity_core.domain.capture import PageCapture, Section
from clarity_core.domain.findings import Category, ElementAnchor, Finding, Severity, Status
from clarity_core.domain.viewport import Viewport
from clarity_persistence.repositories import RunRepository


async def prepared(client: AsyncClient, app: FastAPI, settings: Settings) -> tuple[str, str]:
    site = (
        await client.post(
            "/api/sites", json={"name": "Qiyas", "profile": {"start_url": "theqiyas.cc"}}
        )
    ).json()
    key = (await client.post(f"/api/sites/{site['id']}/extension-key")).json()["key"]
    run_id = (await client.post(f"/api/sites/{site['id']}/runs")).json()["id"]

    async with app.state.sessions() as db:
        runs = RunRepository(db)
        run = await runs.get(uuid.UUID(run_id))
        assert run is not None
        await runs.start(run)
        capture = PageCapture(
            requested_url="https://theqiyas.cc/",
            final_url="https://qiyas.cc/",
            viewport=Viewport.DESKTOP,
            status=200,
            title="Home",
            page_height=2400,
            initial_height=2400,
            sections=[Section(index=0, scroll_y=0, height=900, screenshot="s.png")],
            load_ms=10,
            captured_at=datetime.now(UTC),
        )
        page = await runs.add_page(run, capture)
        page.predictions = {
            "heatmap": f"{run_id}/home/desktop/attention.png",
            "heatmap_scale": 0.25,
            "elements": [
                {
                    "index": 3,
                    "name": "Subscribe",
                    "selector": "#sub",
                    "box": {"x": 1, "y": 2, "width": 3, "height": 4},
                    "click": 0.3,
                    "attention": 0.02,
                }
            ],
        }
        finding = Finding(
            page_url="https://qiyas.cc/",
            viewport=Viewport.DESKTOP,
            category=Category.UX,
            severity=Severity.HIGH,
            status=Status.PREDICTED,
            confidence=0.7,
            title="Weak hero",
            description="d",
            recommendation="r",
            anchor=ElementAnchor(selector="h1"),
        )
        await runs.add_findings(run, [finding], page_id=page.id)
        await runs.complete(run)
        await db.commit()

    heatmap = settings.artifact_dir / run_id / "home" / "desktop" / "attention.png"
    heatmap.parent.mkdir(parents=True)
    heatmap.write_bytes(b"\x89PNG")
    return key, run_id


async def test_extension_reads_the_latest_analysis_with_its_key(
    client: AsyncClient, anonymous: AsyncClient, app: FastAPI, settings: Settings
) -> None:
    key, run_id = await prepared(client, app, settings)
    await client.post("/api/auth/logout")
    headers = {"Authorization": f"Bearer {key}"}

    site = (await anonymous.get("/api/extension/site", headers=headers)).json()
    assert site["run_id"] == run_id
    assert site["pages"][0]["final_url"] == "https://qiyas.cc/"

    data = (
        await anonymous.get(
            "/api/extension/overlay",
            params={"url": "https://www.qiyas.cc/#top", "viewport": "mobile"},
            headers=headers,
        )
    ).json()
    assert data["heatmap"]["src"] == f"/api/extension/artifacts/{run_id}/home/desktop/attention.png"
    assert [note["title"] for note in data["notes"]] == ["Weak hero"]
    assert data["clicks"][0]["anchor"]["selector"] == "#sub"

    image = await anonymous.get(data["heatmap"]["src"], headers=headers)
    assert image.content == b"\x89PNG"


async def test_extension_access_is_scoped(
    client: AsyncClient, anonymous: AsyncClient, app: FastAPI, settings: Settings
) -> None:
    key, _ = await prepared(client, app, settings)
    headers = {"Authorization": f"Bearer {key}"}
    assert (await anonymous.get("/api/extension/site")).status_code == 401
    bad = {"Authorization": "Bearer cc_wrong"}
    assert (await anonymous.get("/api/extension/site", headers=bad)).status_code == 401
    assert (
        await anonymous.get(f"/api/extension/artifacts/{uuid.uuid4()}/x.png", headers=headers)
    ).status_code == 404
    unknown = await anonymous.get(
        "/api/extension/overlay", params={"url": "https://qiyas.cc/nope"}, headers=headers
    )
    assert unknown.status_code == 404
