import uuid
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select

from clarity_api.deps import AppSettings, Session
from clarity_api.security import hash_extension_key
from clarity_core.domain.findings import Finding
from clarity_persistence.models import FindingRecord, PageRecord, Run, RunStatus, Site
from clarity_persistence.repositories import SiteRepository

router = APIRouter(prefix="/extension", tags=["extension"])


class ExtensionPage(BaseModel):
    id: uuid.UUID
    url: str
    final_url: str
    viewport: str


class ExtensionSite(BaseModel):
    name: str
    start_url: str
    run_id: uuid.UUID | None
    pages: list[ExtensionPage]


async def key_site(db: Session, authorization: Annotated[str | None, Header()] = None) -> Site:
    scheme, _, key = (authorization or "").partition(" ")
    site = None
    if scheme.lower() == "bearer" and key:
        site = await SiteRepository(db).by_extension_key_hash(hash_extension_key(key.strip()))
    if site is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid extension key")
    return site


KeySite = Annotated[Site, Depends(key_site)]


async def latest_run(db: Session, site: Site) -> Run | None:
    query = (
        select(Run)
        .where(Run.site_id == site.id, Run.status == RunStatus.COMPLETED)
        .order_by(Run.created_at.desc())
        .limit(1)
    )
    return await db.scalar(query)


@router.get("/site")
async def describe_site(site: KeySite, db: Session) -> ExtensionSite:
    run = await latest_run(db, site)
    pages = []
    if run:
        records = await db.scalars(select(PageRecord).where(PageRecord.run_id == run.id))
        pages = [
            ExtensionPage(
                id=record.id,
                url=record.url,
                final_url=str(record.capture.get("final_url", record.url)),
                viewport=record.viewport,
            )
            for record in records
        ]
    return ExtensionSite(
        name=site.name, start_url=site.start_url, run_id=run.id if run else None, pages=pages
    )


@router.get("/overlay")
async def overlay(
    site: KeySite,
    db: Session,
    url: Annotated[str, Query()],
    viewport: Annotated[str, Query()] = "desktop",
) -> dict[str, Any]:
    run = await latest_run(db, site)
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no completed analysis yet")
    records = list(await db.scalars(select(PageRecord).where(PageRecord.run_id == run.id)))
    wanted = _bare(url)
    candidates = [
        record
        for record in records
        if wanted in {_bare(record.url), _bare(str(record.capture.get("final_url", "")))}
    ]
    if not candidates:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "this page was not part of the analysis")
    page = next((r for r in candidates if r.viewport == viewport), candidates[0])
    findings = await db.scalars(select(FindingRecord).where(FindingRecord.page_id == page.id))
    return _overlay_data(page, [Finding.model_validate(record.data) for record in findings])


@router.get("/artifacts/{key:path}")
async def artifact(key: str, site: KeySite, db: Session, settings: AppSettings) -> FileResponse:
    run = await latest_run(db, site)
    if run is None or not key.startswith(f"{run.id}/"):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "artifact not found")
    root = settings.artifact_dir.resolve()
    path = (root / key).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "artifact not found")
    return FileResponse(Path(path), headers={"Cache-Control": "private, max-age=3600"})


def _overlay_data(page: PageRecord, findings: list[Finding]) -> dict[str, Any]:
    capture = page.capture
    prediction = page.predictions or {}
    sizes = {"desktop": (1440, 900), "tablet": (834, 1112), "mobile": (390, 844)}
    width, height = sizes.get(page.viewport, sizes["desktop"])
    heatmap = (
        {
            "src": f"/api/extension/artifacts/{prediction['heatmap']}",
            "scale": prediction["heatmap_scale"],
        }
        if prediction.get("heatmap")
        else None
    )
    clicks = [
        {
            "index": element["index"],
            "name": element["name"],
            "click": element["click"],
            "attention": element["attention"],
            "anchor": {"selector": element["selector"], "box": element["box"]},
        }
        for element in prediction.get("elements", [])
        if element.get("click")
    ]
    notes = [
        {
            "id": str(finding.id),
            "title": finding.title,
            "description": finding.description,
            "recommendation": finding.recommendation,
            "severity": finding.severity.value,
            "category": finding.category.value,
            "status": finding.status.value,
            "confidence": finding.confidence,
            "anchor": finding.anchor.model_dump(mode="json") if finding.anchor else None,
        }
        for finding in findings
    ]
    return {
        "url": capture.get("final_url", page.url),
        "viewport": {"width": width, "height": height},
        "documentHeight": capture.get("page_height", height),
        "heatmap": heatmap,
        "clicks": clicks,
        "notes": notes,
    }


def _bare(url: str) -> str:
    bare = url.split("#", 1)[0].split("?", 1)[0].rstrip("/")
    for prefix in ("https://", "http://", "www."):
        bare = bare.removeprefix(prefix)
    return bare
