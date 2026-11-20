from dataclasses import dataclass, field

from clarity_ai.provider import MediaType

LANGUAGE_NAMES = {"en": "English", "tr": "Turkish", "az": "Azerbaijani", "ru": "Russian"}


@dataclass(frozen=True)
class ElementLine:
    number: int
    viewport: str
    tag: str
    role: str | None
    name: str
    x: int
    y: int
    width: int
    height: int
    fixed: bool = False
    font_size: float | None = None
    contrast: float | None = None
    attention: float | None = None
    click: float | None = None

    def render(self) -> str:
        parts = [
            f"#{self.number}",
            self.viewport,
            self.role or self.tag,
            f'"{self.name[:80]}"' if self.name else "(no text)",
            f"at {self.x},{self.y} size {self.width}x{self.height}",
        ]
        if self.fixed:
            parts.append("fixed")
        if self.font_size:
            parts.append(f"font {self.font_size:g}px")
        if self.contrast is not None:
            parts.append(f"contrast {self.contrast:.2f}:1")
        if self.attention is not None:
            parts.append(f"attention {self.attention * 100:.1f}%")
        if self.click is not None:
            parts.append(f"predicted clicks {self.click * 100:.0f}%")
        return " | ".join(parts)


@dataclass(frozen=True)
class Shot:
    label: str
    data: bytes
    media_type: MediaType = "image/jpeg"


@dataclass
class PageContext:
    url: str
    title: str
    notes_language: str
    headings: list[str] = field(default_factory=list)
    elements: list[ElementLine] = field(default_factory=list)
    shots: list[Shot] = field(default_factory=list)
    signals: list[str] = field(default_factory=list)

    @property
    def language_name(self) -> str:
        return LANGUAGE_NAMES.get(self.notes_language, "English")

    def element_table(self) -> str:
        return "\n".join(line.render() for line in self.elements) or "(no elements recorded)"

    def outline(self) -> str:
        return "\n".join(f"- {heading}" for heading in self.headings[:40]) or "(no headings)"
