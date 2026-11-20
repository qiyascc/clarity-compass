import math
import re
from dataclasses import dataclass

from clarity_core.domain.prediction import ElementPrediction
from clarity_core.domain.probe import ProbedElement

ACTION_WORDS = re.compile(
    r"\b(buy|order|book|contact|call|get|start|try|sign ?up|register|join|subscribe|download|"
    r"apply|search|send|submit|add to|checkout|request|"
    r"al|satın|sipariş|iletişim|ara|başla|kayıt|üye ol|gönder|"
    r"əlaqə|zəng|axtar|qeydiyyat|göndər|sifariş|"
    r"купить|заказать|связаться|позвонить|начать|регистрация|отправить|поиск)\b",
    re.IGNORECASE,
)
MIN_TAP = 24


@dataclass(frozen=True)
class ClickWeights:
    bias: float = -2.0
    attention: float = 0.9
    size: float = 0.35
    above_fold: float = 0.6
    filled: float = 0.9
    action_text: float = 0.8
    button: float = 0.5
    small_target: float = -0.9
    faint: float = -0.6


class ClickModel:
    """Heuristic click propensity, kept separate from attention.

    Each interactive element gets a logistic score from its attention density,
    size, placement, styling and wording. Scores are then normalised into the
    share of clicks on the page expected to land on each element. A learned
    model trained on real interaction data can replace this behind `score`.
    """

    def __init__(self, weights: ClickWeights | None = None) -> None:
        self.w = weights or ClickWeights()

    def score(
        self,
        elements: list[ProbedElement],
        predictions: list[ElementPrediction],
        *,
        viewport_area: float,
    ) -> list[ElementPrediction]:
        raw: dict[int, float] = {}
        for element, prediction in zip(elements, predictions, strict=True):
            if not element.interactive:
                continue
            raw[prediction.index] = (
                0.0 if element.disabled else self._logit(element, prediction, viewport_area)
            )

        total = sum(raw.values())
        return [
            prediction.model_copy(
                update={"click": (raw[prediction.index] / total if total else 0.0)}
            )
            if prediction.index in raw
            else prediction
            for prediction in predictions
        ]

    def _logit(
        self, element: ProbedElement, prediction: ElementPrediction, viewport_area: float
    ) -> float:
        w = self.w
        box = element.box
        area_share = max(box.width * box.height / viewport_area, 1e-6)
        z = (
            w.bias
            + w.attention * math.log1p(prediction.attention_density)
            + w.size * math.log1p(area_share * 100)
            + w.above_fold * element.above_fold
            + w.filled * _filled(element)
            + w.action_text * bool(ACTION_WORDS.search(element.name or element.text))
            + w.button * (element.role == "button")
            + w.small_target * (min(box.width, box.height) < MIN_TAP)
            + w.faint * (element.contrast is not None and element.contrast < 3)
        )
        return 1 / (1 + math.exp(-z))


def _filled(element: ProbedElement) -> bool:
    background = element.background or ""
    return (
        bool(background)
        and background not in {"rgb(255, 255, 255)", "rgba(0, 0, 0, 0)"}
        and (element.role == "button" or element.font_weight >= 600)
    )
