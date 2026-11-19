import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from clarity_core.domain.capture import PageCapture, Section
from clarity_core.domain.findings import Category, Finding, Severity, Status
from clarity_core.domain.profile import AnalysisProfile, Language
from clarity_core.domain.viewport import Viewport
from clarity_persistence.models import RunStatus
from clarity_persistence.repositories import RunRepository, SiteRepository


def capture(url: str = "https://theqiyas.cc/") -> PageCapture:
    return PageCapture(
        requested_url=url,
        final_url=url,
        viewport=Viewport.DESKTOP,
        status=200,
        title="Home",
        page_height=900,
        initial_height=900,
        sections=[Section(index=0, scroll_y=0, height=900, screenshot="s/0.png")],
        load_ms=120,
        captured_at=datetime.now(UTC),
    )


async def test_site_roundtrip_keeps_the_profile(session: AsyncSession) -> None:
    sites = SiteRepository(session)
    profile = AnalysisProfile(start_url="theqiyas.cc", language=Language.AZ)
    site = await sites.create("Qiyas", profile)
    await session.commit()

    loaded = await sites.get(site.id)
    assert loaded is not None
    assert loaded.start_url == "https://theqiyas.cc/"
    assert AnalysisProfile.model_validate(loaded.profile).language is Language.AZ
    assert [s.id for s in await sites.list()] == [site.id]


async def test_profile_update(session: AsyncSession) -> None:
    sites = SiteRepository(session)
    site = await sites.create("Qiyas", AnalysisProfile(start_url="theqiyas.cc"))
    await sites.update(site, name="Qiyas CC", profile=AnalysisProfile(start_url="qiyas.cc"))
    assert site.name == "Qiyas CC"
    assert site.start_url == "https://qiyas.cc/"


async def test_extension_key_lookup(session: AsyncSession) -> None:
    sites = SiteRepository(session)
    site = await sites.create("Qiyas", AnalysisProfile(start_url="theqiyas.cc"))
    site.extension_key_hash = "abc"
    await session.flush()
    found = await sites.by_extension_key_hash("abc")
    assert found is not None
    assert found.id == site.id
    assert await sites.by_extension_key_hash("nope") is None


async def test_run_lifecycle(session: AsyncSession) -> None:
    site = await SiteRepository(session).create("Q", AnalysisProfile(start_url="theqiyas.cc"))
    runs = RunRepository(session)
    run = await runs.create(site)
    assert run.status is RunStatus.QUEUED
    assert run.profile == site.profile

    await runs.start(run)
    await runs.report(run, stage="explore", pages=3)
    page = await runs.add_page(run, capture())
    finding = Finding(
        page_url="https://theqiyas.cc/",
        viewport=Viewport.DESKTOP,
        category=Category.UX,
        severity=Severity.MEDIUM,
        status=Status.PREDICTED,
        confidence=0.6,
        title="Weak CTA",
        description="d",
        recommendation="r",
    )
    await runs.add_findings(run, [finding], page_id=page.id)
    await runs.complete(run)
    await session.commit()

    loaded = await runs.get(run.id)
    assert loaded is not None
    assert loaded.status is RunStatus.COMPLETED
    assert loaded.progress == {"pages": 3}
    assert loaded.stage == "explore"
    assert loaded.finished_at is not None
    pages = await runs.pages(run.id)
    assert PageCapture.model_validate(pages[0].capture).title == "Home"
    stored = await runs.findings(run.id)
    assert Finding.model_validate(stored[0].data).title == "Weak CTA"


async def test_failed_run_keeps_the_error(session: AsyncSession) -> None:
    site = await SiteRepository(session).create("Q", AnalysisProfile(start_url="theqiyas.cc"))
    runs = RunRepository(session)
    run = await runs.create(site)
    await runs.fail(run, "browser crashed")
    assert run.status is RunStatus.FAILED
    assert run.error == "browser crashed"


async def test_cannot_start_a_finished_run(session: AsyncSession) -> None:
    site = await SiteRepository(session).create("Q", AnalysisProfile(start_url="theqiyas.cc"))
    runs = RunRepository(session)
    run = await runs.create(site)
    await runs.complete(run)
    with pytest.raises(ValueError, match="finished"):
        await runs.start(run)


async def test_missing_run_is_none(session: AsyncSession) -> None:
    assert await RunRepository(session).get(uuid.uuid4()) is None
