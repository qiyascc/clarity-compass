from typing import Any
from urllib.parse import urlsplit

from clarity_ai.agents import RecommendationAgent
from clarity_core.domain.findings import Finding, Status
from clarity_core.domain.report import Priority, Report, summarize

MAX_FINDINGS_FOR_PLAN = 120


async def build_report(
    site: str,
    language: str,
    findings: list[Finding],
    reviews: dict[str, dict[str, Any]],
    recommender: RecommendationAgent | None,
) -> Report:
    report = summarize(findings, reviews)
    if recommender is None or not findings:
        return report

    ranked = sorted(
        findings, key=lambda f: (f.severity.rank, f.status is not Status.VERIFIED, -f.confidence)
    )[:MAX_FINDINGS_FOR_PLAN]
    pages = [
        f"{_path(page.url)} ({page.kind or 'unknown'}): "
        f"{page.purpose or ''} {page.overall or ''}".strip()
        for page in report.pages
    ]
    lines = [_line(finding) for finding in ranked]
    generated = await recommender.run(site, language, pages, lines)
    plan = generated.value
    return report.model_copy(
        update={
            "assessment": plan.assessment,
            "strengths": plan.strengths,
            "priorities": [
                Priority(
                    title=item.title,
                    why=item.why,
                    action=item.action,
                    impact=item.impact,
                    effort=item.effort,
                    finding_ids=[str(ranked[number - 1].id) for number in item.findings],
                )
                for item in plan.priorities
            ],
        }
    )


def _line(finding: Finding) -> str:
    return (
        f"[{finding.severity.value} {finding.status.value} {finding.category.value}] "
        f"{_path(finding.page_url)} ({finding.viewport.value}): {finding.title} - "
        f"{finding.description[:180]}"
    )


def _path(url: str) -> str:
    parts = urlsplit(url)
    return parts.path or "/"
