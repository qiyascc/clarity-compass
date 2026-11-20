from pydantic import BaseModel, Field

from clarity_core.domain.findings import Box


class SectionAttention(BaseModel):
    index: int
    scroll_y: int
    height: int
    combined: str
    windows: dict[str, str]
    agreement: float


class ElementPrediction(BaseModel):
    index: int
    selector: str
    tag: str
    name: str
    box: Box
    interactive: bool
    section: int
    attention: float = Field(ge=0, le=1)
    attention_density: float = Field(ge=0)
    click: float | None = Field(default=None, ge=0, le=1)


class PagePrediction(BaseModel):
    sections: list[SectionAttention]
    heatmap: str
    heatmap_scale: float
    agreement: float
    elements: list[ElementPrediction] = Field(default_factory=list)
    models: list[str] = Field(default_factory=list)

    def top_clicks(self, limit: int = 5) -> list[ElementPrediction]:
        ranked = [element for element in self.elements if element.click is not None]
        return sorted(ranked, key=lambda element: element.click or 0, reverse=True)[:limit]
