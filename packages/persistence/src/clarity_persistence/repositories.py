import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from clarity_core.domain.capture import PageCapture
from clarity_core.domain.findings import Finding
from clarity_core.domain.profile import AnalysisProfile
from clarity_persistence.models import FindingRecord, PageRecord, Run, RunStatus, Site, utcnow


class SiteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, name: str, profile: AnalysisProfile) -> Site:
        site = Site(name=name, start_url=profile.start_url, profile=_dump(profile))
        self.session.add(site)
        await self.session.flush()
        return site

    async def get(self, site_id: uuid.UUID) -> Site | None:
        return await self.session.get(Site, site_id)

    async def list(self) -> Sequence[Site]:
        result = await self.session.scalars(select(Site).order_by(Site.created_at))
        return result.all()

    async def update(
        self, site: Site, *, name: str | None = None, profile: AnalysisProfile | None = None
    ) -> Site:
        if name is not None:
            site.name = name
        if profile is not None:
            site.profile = _dump(profile)
            site.start_url = profile.start_url
        await self.session.flush()
        return site

    async def delete(self, site: Site) -> None:
        await self.session.delete(site)
        await self.session.flush()

    async def by_extension_key_hash(self, key_hash: str) -> Site | None:
        return await self.session.scalar(select(Site).where(Site.extension_key_hash == key_hash))


class RunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, site: Site) -> Run:
        run = Run(site_id=site.id, profile=dict(site.profile), progress={})
        self.session.add(run)
        await self.session.flush()
        return run

    async def get(self, run_id: uuid.UUID) -> Run | None:
        return await self.session.get(Run, run_id)

    async def for_site(self, site_id: uuid.UUID, limit: int = 50) -> Sequence[Run]:
        query = (
            select(Run).where(Run.site_id == site_id).order_by(Run.created_at.desc()).limit(limit)
        )
        return (await self.session.scalars(query)).all()

    async def start(self, run: Run) -> None:
        if run.status.finished:
            raise ValueError(f"run {run.id} already finished")
        run.status = RunStatus.RUNNING
        run.started_at = utcnow()
        await self.session.flush()

    async def report(self, run: Run, *, stage: str | None = None, **progress: Any) -> None:
        if stage is not None:
            run.stage = stage
        run.progress = {**run.progress, **progress}
        await self.session.flush()

    async def complete(self, run: Run) -> None:
        await self._finish(run, RunStatus.COMPLETED)

    async def fail(self, run: Run, error: str) -> None:
        run.error = error
        await self._finish(run, RunStatus.FAILED)

    async def cancel(self, run: Run) -> None:
        await self._finish(run, RunStatus.CANCELLED)

    async def add_page(self, run: Run, capture: PageCapture) -> PageRecord:
        record = PageRecord(
            run_id=run.id,
            url=capture.requested_url,
            viewport=capture.viewport.value,
            status_code=capture.status,
            title=capture.title[:512],
            capture=_dump(capture),
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def pages(self, run_id: uuid.UUID) -> Sequence[PageRecord]:
        query = (
            select(PageRecord).where(PageRecord.run_id == run_id).order_by(PageRecord.created_at)
        )
        return (await self.session.scalars(query)).all()

    async def add_findings(
        self, run: Run, findings: list[Finding], page_id: uuid.UUID | None = None
    ) -> None:
        self.session.add_all(
            FindingRecord(
                id=finding.id,
                run_id=run.id,
                page_id=page_id,
                category=finding.category.value,
                severity=finding.severity.value,
                status=finding.status.value,
                data=_dump(finding),
            )
            for finding in findings
        )
        await self.session.flush()

    async def findings(self, run_id: uuid.UUID) -> Sequence[FindingRecord]:
        query = select(FindingRecord).where(FindingRecord.run_id == run_id)
        return (await self.session.scalars(query)).all()

    async def _finish(self, run: Run, status: RunStatus) -> None:
        run.status = status
        run.finished_at = utcnow()
        await self.session.flush()


def _dump(model: Any) -> dict[str, Any]:
    data: dict[str, Any] = model.model_dump(mode="json")
    return data
