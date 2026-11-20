import re
from enum import StrEnum

from clarity_core.domain.probe import ProbedElement


class Risk(StrEnum):
    SAFE = "safe"
    FORBIDDEN = "forbidden"


FORBIDDEN_WORDS = re.compile(
    r"\b("
    r"delete|remove|destroy|erase|clear all|unsubscribe|deactivate|close account|"
    r"log ?out|sign ?out|pay|purchase|buy now|checkout|place order|order now|confirm|"
    r"publish|post ad|submit|send|transfer|book now|reserve|"
    r"sil|kaldır|çıkış|ödə|öde|satın al|sipariş ver|yayınla|yayımla|gönder|göndər|təsdiq|onayla|"
    r"удалить|выйти|оплатить|купить|оформить|опубликовать|отправить|подтвердить"
    r")\b",
    re.IGNORECASE,
)
FORBIDDEN_HREF = re.compile(r"(logout|log-out|signout|sign-out|delete|remove|unsubscribe)", re.I)
UNSAFE_SCHEMES = ("mailto:", "tel:", "sms:", "javascript:void", "data:")


def classify(element: ProbedElement) -> Risk:
    label = f"{element.name} {element.text}".strip()
    if FORBIDDEN_WORDS.search(label):
        return Risk.FORBIDDEN
    href = element.href or ""
    if FORBIDDEN_HREF.search(href) or href.startswith(UNSAFE_SCHEMES):
        return Risk.FORBIDDEN
    if (
        element.tag == "input"
        and element.role == "button"
        and element.name.lower()
        in {
            "submit",
            "ok",
        }
    ):
        return Risk.FORBIDDEN
    if element.disabled:
        return Risk.FORBIDDEN
    return Risk.SAFE
