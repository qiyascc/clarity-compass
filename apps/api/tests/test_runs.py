import uuid
from datetime import UTC, datetime

from fastapi import FastAPI
from httpx import AsyncClient

from clarity_api.queue import RecordingQueue
from clarity_core.domain.capture import PageCapture, Section
from clarity_core.domain.findings import Category, Finding, Severity, Status
from clarity_core.domain.viewport import Viewport
from clarity_persistence.repositories import RunRepository


async def new_site(client: AsyncClient) -> str:
    response = await client.post(
        "/api/sites", json={"name": "Qiyas", "profile": {"start_url": "theqiyas.cc"}}
    )
    site_id: str = response.json()["id"]
    return site_id


def finding(severity: Severity, category: Category = Category.UX) -> Finding:
    return Finding(
        page_url="https://theqiyas.cc/",
        viewport=Viewport.DESKTOP,
        category=category,
        severity=severity,
        status=Status.PREDICTED,
        confidence=0.5,
        title=f"{severity} issue",
        description="d",
        recommendation="r",
    )


async def test_starting_a_run_enqueues_it(client: AsyncClient, queue: RecordingQueue) -> None:
    site_id = await new_site(client)
    response = await client.post(f"/api/sites/{site_id}/runs")
    assert response.status_code == 202
    run = response.json()
    assert run["status"] == "queued"
    assert queue.enqueued == [uuid.UUID(run["id"])]
    listed = (await client.get(f"/api/sites/{site_id}/runs")).json()
    assert [item["id"] for item in listed] == [run["id"]]


async def test_only_one_active_run_per_site(client: AsyncClient) -> None:
    site_id = await new_site(client)
    await client.post(f"/api/sites/{site_id}/runs")
    assert (await client.post(f"/api/sites/{site_id}/runs")).status_code == 409


async def test_cancel(client: AsyncClient) -> None:
    site_id = await new_site(client)
    run = (await client.post(f"/api/sites/{site_id}/runs")).json()
    cancelled = await client.post(f"/api/runs/{run['id']}/cancel")
    assert cancelled.json()["status"] == "cancelled"
    assert (await client.post(f"/api/runs/{run['id']}/cancel")).status_code == 409
    assert (await client.post(f"/api/sites/{site_id}/runs")).status_code == 202


async def test_pages_and_findings(client: AsyncClient, app: FastAPI) -> None:
    site_id = await new_site(client)
    run_id = (await client.post(f"/api/sites/{site_id}/runs")).json()["id"]

    async with app.state.sessions() as db:
        runs = RunRepository(db)
        run = await runs.get(uuid.UUID(run_id))
        assert run is not None
        capture = PageCapture(
            requested_url="https://theqiyas.cc/",
            final_url="https://qiyas.cc/",
            viewport=Viewport.MOBILE,
            status=200,
            title="Home",
            page_height=844,
            initial_height=844,
            sections=[Section(index=0, scroll_y=0, height=844, screenshot="a.png")],
            load_ms=10,
            captured_at=datetime.now(UTC),
        )
        page = await runs.add_page(run, capture)
        await runs.add_findings(
            run,
            [
                finding(Severity.LOW),
                finding(Severity.CRITICAL, Category.FUNCTIONAL),
                finding(Severity.MEDIUM),
            ],
            page_id=page.id,
        )
        await db.commit()

    pages = (await client.get(f"/api/runs/{run_id}/pages")).json()
    assert pages[0]["viewport"] == "mobile"
    assert pages[0]["capture"]["final_url"] == "https://qiyas.cc/"

    ordered = (await client.get(f"/api/runs/{run_id}/findings")).json()
    assert [item["severity"] for item in ordered] == ["critical", "medium", "low"]

    ux = (await client.get(f"/api/runs/{run_id}/findings", params={"category": "ux"})).json()
    assert {item["category"] for item in ux} == {"ux"}


async def test_unknown_run(client: AsyncClient) -> None:
    assert (await client.get(f"/api/runs/{uuid.uuid4()}")).status_code == 404
