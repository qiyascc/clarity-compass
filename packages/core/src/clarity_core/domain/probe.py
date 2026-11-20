from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from clarity_core.domain.findings import Box


class _Probe(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ProbedElement(_Probe):
    index: int
    tag: str
    role: str | None
    name: str
    text: str
    selector: str
    xpath: str
    box: Box
    visible: bool
    above_fold: bool
    position: str
    interactive: bool
    href: str | None
    disabled: bool
    font_size: float
    font_weight: int
    color: str | None
    background: str | None
    contrast: float | None
    background_image: bool


class ProbedImage(_Probe):
    selector: str
    src: str
    alt: str | None
    box: Box
    loaded: bool
    natural_width: int
    natural_height: int
    lazy: bool


class ProbedField(_Probe):
    selector: str
    tag: str
    type: str
    name: str | None
    label: str | None
    required: bool
    autocomplete: str | None
    sensitive: bool
    box: Box


class ProbedForm(_Probe):
    selector: str
    action: str | None
    method: str
    fields: list[ProbedField]
    submit_text: str | None


class Heading(_Probe):
    level: int
    text: str
    selector: str


class ViewportSize(_Probe):
    width: int
    height: int


class PageProbe(_Probe):
    url: str
    title: str
    lang: str | None
    viewport_meta: str | None
    viewport: ViewportSize
    document_height: int
    document_width: int = 0
    overflowing: list[str] = Field(default_factory=list)
    headings: list[Heading] = Field(default_factory=list)
    elements: list[ProbedElement] = Field(default_factory=list)
    images: list[ProbedImage] = Field(default_factory=list)
    forms: list[ProbedForm] = Field(default_factory=list)
    landmarks: dict[str, list[Box]] = Field(default_factory=dict)
    truncated: bool = False

    @property
    def interactive(self) -> list[ProbedElement]:
        return [element for element in self.elements if element.interactive and element.visible]
