from clarity_core.domain.capture import PageCapture
from clarity_core.domain.findings import Finding
from clarity_core.domain.probe import PageProbe
from clarity_worker.checks.rules import RULES, Page

SiteKey = tuple[str, str, str]


def run_checks(
    captures: list[tuple[PageCapture, PageProbe]],
    language: str,
    reported: set[SiteKey] | None = None,
) -> list[Finding]:
    """Runs every rule on each viewport of one page.

    Repeats across viewports are dropped, and so are element findings already in
    `reported`, which callers share between pages so that site-wide parts such as
    the header and footer are reported once per run. Selectors differ between
    pages for the same element, so it is recognised by its text and placement.
    """
    reported = reported if reported is not None else set()
    findings: list[Finding] = []
    seen: set[tuple[str, str | None]] = set()
    for index, (capture, probe) in enumerate(captures):
        page = Page(capture, probe, language, primary=index == 0)
        for rule in RULES:
            for finding in rule(page):
                selector = finding.anchor.selector if finding.anchor else None
                key = (finding.source, selector)
                if key in seen and finding.source != "check:small-tap-target":
                    continue
                seen.add(key)
                findings.append(finding)
    return drop_reported(findings, reported)


def drop_reported(findings: list[Finding], reported: set[SiteKey]) -> list[Finding]:
    kept = []
    for finding in findings:
        anchor = finding.anchor
        if anchor and (anchor.box or anchor.selector):
            box = anchor.box
            placement = (
                f"{box.x:.0f},{box.y:.0f},{box.width:.0f}x{box.height:.0f}"
                if box
                else f"selector {anchor.selector}"
            )
            site_key = (finding.source, anchor.text or "", placement)
            if site_key in reported:
                continue
            reported.add(site_key)
        kept.append(finding)
    return kept
