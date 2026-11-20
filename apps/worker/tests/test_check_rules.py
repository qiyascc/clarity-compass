from datetime import UTC, datetime

from clarity_core.domain.capture import PageCapture, Section
from clarity_core.domain.findings import Box, Finding
from clarity_core.domain.probe import (
    Heading,
    PageProbe,
    ProbedElement,
    ProbedField,
    ProbedForm,
    ViewportSize,
)
from clarity_core.domain.viewport import Viewport
from clarity_worker.checks import run_checks


def element(index: int, **overrides: object) -> ProbedElement:
    fields: dict[str, object] = {
        "index": index,
        "tag": "a",
        "role": "link",
        "name": "work",
        "text": "work",
        "selector": f"#e{index}",
        "xpath": f"/html/body/a[{index}]",
        "box": Box(x=10, y=10, width=32, height=17),
        "visible": True,
        "above_fold": True,
        "position": "static",
        "interactive": True,
        "href": "https://shop.test/work",
        "disabled": False,
        "font_size": 14,
        "font_weight": 400,
        "color": "rgb(20, 20, 20)",
        "background": "rgb(255, 255, 255)",
        "contrast": 18.0,
        "background_image": False,
    }
    fields.update(overrides)
    return ProbedElement.model_validate(fields)


def page(
    elements: list[ProbedElement],
    forms: list[ProbedForm] | None = None,
    url: str = "https://shop.test/",
) -> tuple[PageCapture, PageProbe]:
    capture = PageCapture(
        requested_url=url,
        final_url=url,
        viewport=Viewport.MOBILE,
        status=200,
        title="t",
        page_height=844,
        initial_height=844,
        sections=[Section(index=0, scroll_y=0, height=844, screenshot="s.png")],
        load_ms=100,
        captured_at=datetime.now(UTC),
    )
    probe = PageProbe(
        url=url,
        title="t",
        lang="en",
        viewport_meta="width=device-width",
        viewport=ViewportSize(width=390, height=844),
        document_height=844,
        headings=[Heading(level=1, text="Shop", selector="h1")],
        elements=elements,
        forms=forms or [],
    )
    return capture, probe


def sources(findings: list[Finding]) -> list[str]:
    return [finding.source for finding in findings]


def test_transparent_text_and_hidden_skip_links_are_ignored() -> None:
    gradient = element(1, tag="span", interactive=False, color="rgba(0, 0, 0, 0)", contrast=1.0)
    skip = element(2, name="Skip to content", box=Box(x=0, y=0, width=1, height=1))
    findings = run_checks([page([gradient, skip])], "en")
    assert "check:low-contrast" not in sources(findings)
    assert "check:small-tap-target" not in sources(findings)


def test_labelled_checkboxes_are_not_small_targets() -> None:
    checkbox = element(
        3, tag="input", role="checkbox", name="I agree", box=Box(x=0, y=0, width=16, height=16)
    )
    form = ProbedForm(
        selector="form",
        action=None,
        method="post",
        submit_text="Send",
        fields=[
            ProbedField(
                selector="#e3",
                tag="input",
                type="checkbox",
                name="consent",
                label="I agree",
                required=True,
                autocomplete=None,
                sensitive=False,
                box=Box(x=0, y=0, width=16, height=16),
            )
        ],
    )
    assert "check:small-tap-target" not in sources(run_checks([page([checkbox], [form])], "en"))


def test_site_wide_elements_are_reported_once_per_run() -> None:
    reported: set[tuple[str, str, str]] = set()
    nav = element(4)
    first = run_checks([page([nav])], "en", reported)
    second = run_checks([page([nav], url="https://shop.test/about")], "en", reported)
    assert sources(first) == ["check:small-tap-target"]
    assert second == []
