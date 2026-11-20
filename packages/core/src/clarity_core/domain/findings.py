from enum import StrEnum
from typing import Self
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator

from clarity_core.domain.viewport import Viewport


class Category(StrEnum):
    VISUAL = "visual"
    UX = "ux"
    FUNCTIONAL = "functional"
    CONTENT = "content"
    CONVERSION = "conversion"
    ACCESSIBILITY = "accessibility"
    PERFORMANCE = "performance"


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SUGGESTION = "suggestion"

    @property
    def rank(self) -> int:
        return list(Severity).index(self)


class Status(StrEnum):
    VERIFIED = "verified"
    PREDICTED = "predicted"


class EvidenceKind(StrEnum):
    SCREENSHOT = "screenshot"
    ACTION_TRACE = "action_trace"
    CONSOLE = "console"
    NETWORK = "network"
    DOM = "dom"
    METRIC = "metric"


OBSERVED_FAILURES = frozenset(
    {EvidenceKind.ACTION_TRACE, EvidenceKind.NETWORK, EvidenceKind.CONSOLE}
)


class Box(BaseModel):
    x: float
    y: float
    width: float = Field(ge=0)
    height: float = Field(ge=0)

    @property
    def center(self) -> tuple[float, float]:
        return self.x + self.width / 2, self.y + self.height / 2


class ElementAnchor(BaseModel):
    selector: str | None = None
    xpath: str | None = None
    text: str | None = None
    role: str | None = None
    box: Box | None = None


class Evidence(BaseModel):
    kind: EvidenceKind
    ref: str
    summary: str | None = None


class Finding(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    page_url: str
    viewport: Viewport
    category: Category
    severity: Severity
    status: Status
    confidence: float = Field(ge=0, le=1)
    title: str = Field(min_length=1, max_length=200)
    description: str
    recommendation: str
    alternative: str | None = None
    anchor: ElementAnchor | None = None
    evidence: list[Evidence] = Field(default_factory=list)
    source: str = "unknown"

    @property
    def is_verified(self) -> bool:
        return self.status is Status.VERIFIED

    @model_validator(mode="after")
    def _verified_needs_proof(self) -> Self:
        if not self.is_verified:
            return self
        if not self.evidence:
            raise ValueError("verified findings need evidence")
        kinds = {item.kind for item in self.evidence}
        if self.category is Category.FUNCTIONAL and not kinds & OBSERVED_FAILURES:
            raise ValueError(
                "verified functional findings need an action trace or an observed network "
                "or console failure"
            )
        return self
