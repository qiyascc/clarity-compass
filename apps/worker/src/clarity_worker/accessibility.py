import contextlib
from typing import Any

from playwright.async_api import Error as PlaywrightError

from clarity_core.domain.findings import (
    Category,
    ElementAnchor,
    Evidence,
    EvidenceKind,
    Finding,
    Severity,
    Status,
)
from clarity_core.domain.viewport import Viewport
from clarity_worker.browser import GuardedContext
from clarity_worker.probe import run_axe

IMPACT = {
    "critical": Severity.HIGH,
    "serious": Severity.HIGH,
    "moderate": Severity.MEDIUM,
    "minor": Severity.LOW,
}
NODES_PER_RULE = 3


async def audit_accessibility(context: GuardedContext, url: str, language: str) -> list[Finding]:
    """Runs axe-core on the loaded page; every violation it reports is a measured fact."""
    page = await context.new_page()
    try:
        await page.goto(url, wait_until="load", timeout=30_000)
        with contextlib.suppress(PlaywrightError):
            await page.wait_for_load_state("networkidle", timeout=4_000)
        violations = await run_axe(page, language)
    finally:
        await page.close()
    return [
        finding
        for violation in violations
        for finding in to_findings(violation, page.url, context.viewport)
    ]


def to_findings(violation: dict[str, Any], page_url: str, viewport: Viewport) -> list[Finding]:
    severity = IMPACT.get(violation.get("impact") or "", Severity.MEDIUM)
    findings = []
    for node in violation["nodes"][:NODES_PER_RULE]:
        findings.append(
            Finding(
                page_url=page_url,
                viewport=viewport,
                category=Category.ACCESSIBILITY,
                severity=severity,
                status=Status.VERIFIED,
                confidence=0.9,
                title=violation["help"][:200],
                description=violation["description"],
                recommendation=f"{node['summary'].strip()}\n{violation['helpUrl']}".strip(),
                anchor=ElementAnchor(selector=node["target"]),
                evidence=[
                    Evidence(kind=EvidenceKind.DOM, ref=node["target"], summary=node["html"])
                ],
                source=f"axe:{violation['id']}",
            )
        )
    return findings
