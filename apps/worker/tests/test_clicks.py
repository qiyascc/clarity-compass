import pytest

from clarity_core.domain.findings import Box
from clarity_core.domain.prediction import ElementPrediction
from clarity_core.domain.probe import ProbedElement
from clarity_worker.clicks import ClickModel


def element(index: int, name: str, box: Box, **overrides: object) -> ProbedElement:
    fields: dict[str, object] = {
        "index": index,
        "tag": "a",
        "role": "link",
        "name": name,
        "text": name,
        "selector": f"#e{index}",
        "xpath": f"/html/body/a[{index}]",
        "box": box,
        "visible": True,
        "above_fold": True,
        "position": "static",
        "interactive": True,
        "href": "https://shop.test/x",
        "disabled": False,
        "font_size": 16,
        "font_weight": 400,
        "color": "rgb(20, 20, 20)",
        "background": "rgb(255, 255, 255)",
        "contrast": 15.0,
        "background_image": False,
    }
    fields.update(overrides)
    return ProbedElement.model_validate(fields)


def prediction(item: ProbedElement, attention: float) -> ElementPrediction:
    area = item.box.width * item.box.height
    return ElementPrediction(
        index=item.index,
        selector=item.selector,
        tag=item.tag,
        name=item.name,
        box=item.box,
        interactive=True,
        section=0,
        attention=attention,
        attention_density=attention / (area / (1440 * 900)),
    )


def test_click_shares_sum_to_one_and_favour_prominent_ctas() -> None:
    cta = element(
        1,
        "Contact agent",
        Box(x=600, y=400, width=220, height=52),
        tag="button",
        role="button",
        href=None,
        font_weight=600,
        background="rgb(15, 118, 110)",
        color="rgb(255, 255, 255)",
    )
    footer = element(2, "Privacy", Box(x=40, y=860, width=60, height=14), font_size=11)
    nav = element(3, "About", Box(x=1200, y=20, width=60, height=20))
    elements = [cta, footer, nav]
    predictions = [prediction(cta, 0.12), prediction(footer, 0.002), prediction(nav, 0.02)]

    scored = ClickModel().score(elements, predictions, viewport_area=1440 * 900)

    shares = {item.name: item.click or 0 for item in scored}
    assert sum(shares.values()) == pytest.approx(1)
    assert shares["Contact agent"] > shares["About"] > shares["Privacy"]


def test_disabled_elements_get_no_clicks() -> None:
    live = element(1, "Buy", Box(x=0, y=0, width=100, height=40))
    dead = element(2, "Buy", Box(x=0, y=60, width=100, height=40), disabled=True)
    scored = ClickModel().score(
        [live, dead], [prediction(live, 0.1), prediction(dead, 0.1)], viewport_area=1440 * 900
    )
    assert scored[1].click == 0
    assert scored[0].click == pytest.approx(1)


def test_non_interactive_elements_are_left_alone() -> None:
    text = element(
        1, "", Box(x=0, y=0, width=300, height=40), interactive=False, tag="p", role=None
    )
    scored = ClickModel().score([text], [prediction(text, 0.3)], viewport_area=1440 * 900)
    assert scored[0].click is None
