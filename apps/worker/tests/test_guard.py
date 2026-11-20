import pytest

from clarity_core.domain.findings import Box
from clarity_core.domain.probe import ProbedElement
from clarity_worker.functional.guard import Risk, classify


def element(
    name: str, *, tag: str = "button", href: str | None = None, **extra: object
) -> ProbedElement:
    fields: dict[str, object] = {
        "index": 1,
        "tag": tag,
        "role": "button" if tag != "a" else "link",
        "name": name,
        "text": name,
        "selector": "#x",
        "xpath": "/html/body/button",
        "box": Box(x=0, y=0, width=100, height=40),
        "visible": True,
        "above_fold": True,
        "position": "static",
        "interactive": True,
        "href": href,
        "disabled": False,
        "font_size": 16,
        "font_weight": 400,
        "color": None,
        "background": None,
        "contrast": None,
        "background_image": False,
    }
    fields.update(extra)
    return ProbedElement.model_validate(fields)


@pytest.mark.parametrize(
    "name",
    [
        "Delete listing",
        "Log out",
        "Buy now",
        "Place order",
        "Send message",
        "Elanı sil",
        "Elanı yayımla",
        "Satın al",
        "Göndər",
        "Удалить",
        "Оплатить",
    ],
)
def test_destructive_and_outward_actions_are_forbidden(name: str) -> None:
    assert classify(element(name)) is Risk.FORBIDDEN


@pytest.mark.parametrize(
    "name", ["Search", "Menu", "EN", "Show more", "Axtar", "Ətraflı", "Filters"]
)
def test_exploratory_actions_are_safe(name: str) -> None:
    assert classify(element(name)) is Risk.SAFE


def test_risky_links_and_disabled_controls_are_forbidden() -> None:
    assert classify(element("Account", tag="a", href="https://x.test/logout")) is Risk.FORBIDDEN
    assert classify(element("Call us", tag="a", href="tel:+994")) is Risk.FORBIDDEN
    assert classify(element("Next", disabled=True)) is Risk.FORBIDDEN
    assert classify(element("About", tag="a", href="https://x.test/about")) is Risk.SAFE
