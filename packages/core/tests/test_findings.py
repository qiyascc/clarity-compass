import pytest
from pydantic import ValidationError

from clarity_core.domain.findings import (
    Box,
    Category,
    ElementAnchor,
    Evidence,
    EvidenceKind,
    Finding,
    Severity,
    Status,
)
from clarity_core.domain.viewport import Viewport

ANCHOR = ElementAnchor(
    selector="#contact",
    xpath="/html/body/main/button[2]",
    text="Contact agent",
    role="button",
    box=Box(x=40, y=2210, width=180, height=44),
)


def finding(**overrides: object) -> Finding:
    fields: dict[str, object] = {
        "page_url": "https://theqiyas.cc/listing/1",
        "viewport": Viewport.DESKTOP,
        "category": Category.UX,
        "severity": Severity.HIGH,
        "status": Status.PREDICTED,
        "confidence": 0.7,
        "title": "Contact button is far from the price",
        "description": "Visitors see the price at the top but the button sits below the fold.",
        "recommendation": "Move the contact button next to the price block.",
        "anchor": ANCHOR,
    }
    fields.update(overrides)
    return Finding.model_validate(fields)


def test_predicted_finding_needs_no_evidence() -> None:
    assert finding().evidence == []


def test_verified_finding_requires_evidence() -> None:
    with pytest.raises(ValidationError, match="evidence"):
        finding(status=Status.VERIFIED)


def test_verified_functional_finding_requires_observed_failure() -> None:
    screenshot = Evidence(kind=EvidenceKind.SCREENSHOT, ref="shots/1.png")
    with pytest.raises(ValidationError, match="action trace"):
        finding(category=Category.FUNCTIONAL, status=Status.VERIFIED, evidence=[screenshot])


def test_observed_network_failure_verifies_a_functional_finding() -> None:
    response = Evidence(kind=EvidenceKind.NETWORK, ref="GET /img/missing.jpg 404")
    result = finding(category=Category.FUNCTIONAL, status=Status.VERIFIED, evidence=[response])
    assert result.is_verified


def test_verified_functional_finding_with_trace_is_accepted() -> None:
    trace = Evidence(kind=EvidenceKind.ACTION_TRACE, ref="traces/7.json", summary="click #lang")
    result = finding(category=Category.FUNCTIONAL, status=Status.VERIFIED, evidence=[trace])
    assert result.is_verified


def test_confidence_is_bounded() -> None:
    with pytest.raises(ValidationError):
        finding(confidence=1.2)


def test_severity_ordering() -> None:
    assert Severity.CRITICAL.rank < Severity.HIGH.rank < Severity.SUGGESTION.rank


def test_box_center() -> None:
    assert ANCHOR.box is not None
    assert ANCHOR.box.center == (130, 2232)
