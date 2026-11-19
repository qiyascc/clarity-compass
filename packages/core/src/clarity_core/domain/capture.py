from datetime import datetime

from pydantic import BaseModel, Field

from clarity_core.domain.viewport import Viewport


class Section(BaseModel):
    index: int
    scroll_y: int
    height: int
    screenshot: str


class ConsoleEntry(BaseModel):
    level: str
    text: str
    location: str | None = None


class RequestIssue(BaseModel):
    url: str
    method: str
    resource_type: str
    status: int | None = None
    error: str | None = None


class PageCapture(BaseModel):
    requested_url: str
    final_url: str
    viewport: Viewport
    status: int | None
    title: str
    page_height: int
    initial_height: int
    sections: list[Section]
    full_page: str | None = None
    links: list[str] = Field(default_factory=list)
    console: list[ConsoleEntry] = Field(default_factory=list)
    page_errors: list[str] = Field(default_factory=list)
    request_issues: list[RequestIssue] = Field(default_factory=list)
    blocked_requests: list[RequestIssue] = Field(default_factory=list)
    load_ms: int
    captured_at: datetime

    @property
    def grew_while_scrolling(self) -> bool:
        return self.page_height > self.initial_height
