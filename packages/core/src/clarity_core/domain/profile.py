from enum import StrEnum
from typing import Self

from pydantic import BaseModel, Field, field_validator, model_validator

from clarity_core.domain.viewport import Viewport
from clarity_core.net.urls import normalize_url, same_site


class ScopeMode(StrEnum):
    SITE = "site"
    PAGES = "pages"
    SINGLE = "single"


class Language(StrEnum):
    EN = "en"
    TR = "tr"
    AZ = "az"
    RU = "ru"


class CrawlLimits(BaseModel):
    max_pages: int = Field(default=25, ge=1, le=500)
    max_depth: int = Field(default=3, ge=0, le=10)
    max_actions_per_page: int = Field(default=40, ge=0, le=500)


class AnalysisProfile(BaseModel):
    start_url: str
    scope: ScopeMode = ScopeMode.SITE
    pages: list[str] = Field(default_factory=list)
    exclude_patterns: list[str] = Field(default_factory=list)
    viewports: list[Viewport] = Field(default_factory=lambda: [Viewport.DESKTOP, Viewport.MOBILE])
    language: Language = Language.EN
    limits: CrawlLimits = Field(default_factory=CrawlLimits)

    @field_validator("start_url")
    @classmethod
    def _normalize_start(cls, value: str) -> str:
        return normalize_url(value)

    @field_validator("pages")
    @classmethod
    def _normalize_pages(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(normalize_url(page) for page in value))

    @field_validator("viewports")
    @classmethod
    def _unique_viewports(cls, value: list[Viewport]) -> list[Viewport]:
        if not value:
            raise ValueError("at least one viewport is required")
        return list(dict.fromkeys(value))

    @model_validator(mode="after")
    def _check_scope(self) -> Self:
        if self.scope is ScopeMode.PAGES and not self.pages:
            raise ValueError("pages scope needs at least one page")
        foreign = [page for page in self.pages if not same_site(page, self.start_url)]
        if foreign:
            raise ValueError(f"pages outside the site: {', '.join(foreign)}")
        if self.scope is ScopeMode.SINGLE:
            self.limits = self.limits.model_copy(update={"max_pages": 1, "max_depth": 0})
        return self

    def seed_urls(self) -> list[str]:
        if self.scope is ScopeMode.PAGES:
            return self.pages
        return [self.start_url]
