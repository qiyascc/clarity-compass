import uuid

from fastapi import FastAPI
from httpx import AsyncClient

from clarity_api.queue import RecordingQueue
from clarity_core.domain.findings import Category, ElementAnchor, Finding, Severity, Status
from clarity_core.domain.viewport import Viewport
from clarity_persistence.repositories import RunRepository, SimulationRepository


async def stored_findings(client: AsyncClient, app: FastAPI) -> tuple[str, str]:
    site = (
        await client.post("/api/sites", json={"name": "Q", "profile": {"start_url": "theqiyas.cc"}})
    ).json()
    run_id = (await client.post(f"/api/sites/{site['id']}/runs")).json()["id"]
    anchored = Finding(
        page_url="https://qiyas.cc/",
        viewport=Viewport.DESKTOP,
        category=Category.CONVERSION,
        severity=Severity.HIGH,
        status=Status.PREDICTED,
        confidence=0.7,
        title="CTA is weak",
        description="d",
        recommendation="r",
        anchor=ElementAnchor(selector="#cta"),
    )
    loose = anchored.model_copy(update={"id": uuid.uuid4(), "anchor": None})
    async with app.state.sessions() as db:
        runs = RunRepository(db)
        run = await runs.get(uuid.UUID(run_id))
        assert run is not None
        await runs.add_findings(run, [anchored, loose])
        await db.commit()
    return str(anchored.id), str(loose.id)


async def test_simulations_are_queued_and_readable(
    client: AsyncClient, app: FastAPI, queue: RecordingQueue
) -> None:
    anchored, loose = await stored_findings(client, app)
    created = await client.post(f"/api/findings/{anchored}/simulations")
    assert created.status_code == 202
    simulation = created.json()
    assert simulation["status"] == "queued"
    assert queue.simulations == [uuid.UUID(simulation["id"])]

    async with app.state.sessions() as db:
        simulations = SimulationRepository(db)
        stored = await simulations.get(uuid.UUID(simulation["id"]))
        assert stored is not None
        await simulations.finish(stored, patch={"css": "#cta{}"}, result={"change": 0.02})
        await db.commit()

    done = (await client.get(f"/api/simulations/{simulation['id']}")).json()
    assert done["status"] == "completed"
    assert done["result"] == {"change": 0.02}
    listed = (await client.get(f"/api/findings/{anchored}/simulations")).json()
    assert [item["id"] for item in listed] == [simulation["id"]]

    assert (await client.post(f"/api/findings/{loose}/simulations")).status_code == 422
    assert (await client.post(f"/api/findings/{uuid.uuid4()}/simulations")).status_code == 404
