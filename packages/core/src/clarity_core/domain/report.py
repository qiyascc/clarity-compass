from collections import Counter
from statistics import mean
from typing import Any

from pydantic import BaseModel, Field

from clarity_core.domain.findings import Finding, Severity, Status

SCORE_AREAS = ("visual", "ux", "content", "conversion", "accessibility")


class PageSummary(BaseModel):
    url: str
    kind: str | None = None
    purpose: str | None = None
    overall: str | None = None
    scores: dict[str, int] = Field(default_factory=dict)
    findings: int = 0
    critical: int = 0


class Priority(BaseModel):
    title: str
    why: str
    action: str
    impact: str
    effort: str
    finding_ids: list[str] = Field(default_factory=list)


class Report(BaseModel):
    scores: dict[str, int]
    totals: dict[str, int]
    by_severity: dict[str, int]
    by_category: dict[str, int]
    verified: int
    predicted: int
    pages: list[PageSummary]
    top_findings: list[str]
    assessment: str | None = None
    strengths: list[str] = Field(default_factory=list)
    priorities: list[Priority] = Field(default_factory=list)


def summarize(findings: list[Finding], reviews: dict[str, dict[str, Any]]) -> Report:
    by_url: dict[str, list[Finding]] = {}
    for finding in findings:
        by_url.setdefault(finding.page_url, []).append(finding)

    pages = []
    for url in dict.fromkeys([*reviews, *by_url]):
        review = reviews.get(url) or {}
        understanding = review.get("understanding") or {}
        page_findings = by_url.get(url, [])
        pages.append(
            PageSummary(
                url=url,
                kind=understanding.get("kind"),
                purpose=understanding.get("purpose"),
                overall=review.get("overall"),
                scores=review.get("scores") or {},
                findings=len(page_findings),
                critical=sum(f.severity is Severity.CRITICAL for f in page_findings),
            )
        )

    scored = [page.scores for page in pages if page.scores]
    scores = {
        area: round(mean(score[area] for score in scored if area in score))
        for area in SCORE_AREAS
        if any(area in score for score in scored)
    }
    ranked = sorted(
        findings,
        key=lambda f: (f.severity.rank, f.status is not Status.VERIFIED, -f.confidence),
    )
    return Report(
        scores=scores,
        totals={"pages": len(pages), "findings": len(findings)},
        by_severity=dict(Counter(f.severity.value for f in findings)),
        by_category=dict(Counter(f.category.value for f in findings)),
        verified=sum(f.is_verified for f in findings),
        predicted=sum(not f.is_verified for f in findings),
        pages=pages,
        top_findings=[str(f.id) for f in ranked[:10]],
    )
