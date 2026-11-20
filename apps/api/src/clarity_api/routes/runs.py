import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from clarity_api.deps import CurrentUser, Queue, Session
from clarity_api.routes.sites import load_site
from clarity_api.schemas import PageOut, RunOut
from clarity_core.domain.findings import Category, Finding, Severity, Status
from clarity_persistence.models import Run, RunStatus
from clarity_persistence.repositories import RunRepository

router = APIRouter(tags=["runs"])

ACTIVE = (RunStatus.QUEUED, RunStatus.RUNNING)


async def load_run(db: Session, run_id: uuid.UUID) -> Run:
    run = await RunRepository(db).get(run_id)
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "run not found")
    return run


@router.post("/sites/{site_id}/runs", status_code=status.HTTP_202_ACCEPTED)
async def start_run(site_id: uuid.UUID, db: Session, queue: Queue, _: CurrentUser) -> RunOut:
    site = await load_site(db, site_id)
    busy = await db.scalar(select(Run.id).where(Run.site_id == site.id, Run.status.in_(ACTIVE)))
    if busy is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "an analysis is already in progress")
    run = await RunRepository(db).create(site)
    await db.commit()
    await db.refresh(run)
    await queue.enqueue(run.id)
    return RunOut.of(run)


@router.get("/sites/{site_id}/runs")
async def list_runs(site_id: uuid.UUID, db: Session, _: CurrentUser) -> list[RunOut]:
    await load_site(db, site_id)
    return [RunOut.of(run) for run in await RunRepository(db).for_site(site_id)]


@router.get("/runs/{run_id}")
async def get_run(run_id: uuid.UUID, db: Session, _: CurrentUser) -> RunOut:
    return RunOut.of(await load_run(db, run_id))


@router.post("/runs/{run_id}/cancel")
async def cancel_run(run_id: uuid.UUID, db: Session, _: CurrentUser) -> RunOut:
    run = await load_run(db, run_id)
    if run.status.finished:
        raise HTTPException(status.HTTP_409_CONFLICT, "run already finished")
    await RunRepository(db).cancel(run)
    return RunOut.of(run)


@router.get("/runs/{run_id}/pages")
async def list_pages(run_id: uuid.UUID, db: Session, _: CurrentUser) -> list[PageOut]:
    await load_run(db, run_id)
    return [PageOut.of(page) for page in await RunRepository(db).pages(run_id)]


@router.get("/runs/{run_id}/findings")
async def list_findings(
    run_id: uuid.UUID,
    db: Session,
    _: CurrentUser,
    category: Annotated[list[Category] | None, Query()] = None,
    severity: Annotated[list[Severity] | None, Query()] = None,
    finding_status: Annotated[Status | None, Query(alias="status")] = None,
) -> list[Finding]:
    await load_run(db, run_id)
    findings = [Finding.model_validate(r.data) for r in await RunRepository(db).findings(run_id)]
    selected = [
        finding
        for finding in findings
        if (not category or finding.category in category)
        and (not severity or finding.severity in severity)
        and (finding_status is None or finding.status is finding_status)
    ]
    return sorted(selected, key=lambda finding: (finding.severity.rank, -finding.confidence))
