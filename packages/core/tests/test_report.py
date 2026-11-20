from typing import Any

from clarity_core.domain.findings import Category, Finding, Severity, Status
from clarity_core.domain.report import summarize
from clarity_core.domain.viewport import Viewport


def finding(
    url: str, severity: Severity, status: Status = Status.PREDICTED, confidence: float = 0.5
) -> Finding:
    fields: dict[str, object] = {
        "page_url": url,
        "viewport": Viewport.DESKTOP,
        "category": Category.UX,
        "severity": severity,
        "status": status,
        "confidence": confidence,
        "title": severity.value,
        "description": "d",
        "recommendation": "r",
    }
    if status is Status.VERIFIED:
        fields["evidence"] = [{"kind": "metric", "ref": "x"}]
    return Finding.model_validate(fields)


def test_summary_counts_ranks_and_averages() -> None:
    home, about = "https://shop.test/", "https://shop.test/about"
    findings = [
        finding(home, Severity.LOW),
        finding(home, Severity.CRITICAL, confidence=0.6),
        finding(about, Severity.CRITICAL, Status.VERIFIED),
        finding(about, Severity.HIGH, confidence=0.9),
    ]
    reviews: dict[str, dict[str, Any]] = {
        home: {
            "understanding": {"kind": "home", "purpose": "Sell flats"},
            "overall": "ok",
            "scores": {
                "visual": 60,
                "ux": 50,
                "content": 40,
                "conversion": 30,
                "accessibility": 70,
            },
        },
        about: {
            "scores": {"visual": 80, "ux": 70, "content": 60, "conversion": 50, "accessibility": 90}
        },
    }
    report = summarize(findings, reviews)

    assert report.scores == {
        "visual": 70,
        "ux": 60,
        "content": 50,
        "conversion": 40,
        "accessibility": 80,
    }
    assert report.totals == {"pages": 2, "findings": 4}
    assert report.by_severity == {"low": 1, "critical": 2, "high": 1}
    assert (report.verified, report.predicted) == (1, 3)
    assert report.top_findings[:2] == [str(findings[2].id), str(findings[1].id)]
    assert report.pages[0].kind == "home"
    assert report.pages[1].critical == 1


def test_empty_run() -> None:
    report = summarize([], {})
    assert report.scores == {}
    assert report.totals == {"pages": 0, "findings": 0}
