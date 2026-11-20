from clarity_core.domain.capture import PageCapture
from clarity_core.domain.findings import Finding
from clarity_core.domain.probe import PageProbe
from clarity_worker.checks.rules import RULES, Page


def run_checks(captures: list[tuple[PageCapture, PageProbe]], language: str) -> list[Finding]:
    """Runs every rule on each viewport of one page and drops repeats across viewports."""
    findings: list[Finding] = []
    seen: set[tuple[str, str | None]] = set()
    for index, (capture, probe) in enumerate(captures):
        page = Page(capture, probe, language, primary=index == 0)
        for rule in RULES:
            for finding in rule(page):
                key = (finding.source, finding.anchor.selector if finding.anchor else None)
                if key in seen and finding.source != "check:small-tap-target":
                    continue
                seen.add(key)
                findings.append(finding)
    return findings
