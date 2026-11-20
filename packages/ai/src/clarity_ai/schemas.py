from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class PageKind(StrEnum):
    HOME = "home"
    LISTING_INDEX = "listing_index"
    LISTING_DETAIL = "listing_detail"
    PRODUCT = "product"
    CATEGORY = "category"
    SEARCH = "search"
    ABOUT = "about"
    CONTACT = "contact"
    LOGIN = "login"
    REGISTER = "register"
    ACCOUNT = "account"
    CHECKOUT = "checkout"
    PRICING = "pricing"
    ARTICLE = "article"
    BLOG_INDEX = "blog_index"
    PORTFOLIO = "portfolio"
    LEGAL = "legal"
    ERROR = "error"
    OTHER = "other"


class PageUnderstanding(BaseModel):
    kind: PageKind
    purpose: str = Field(description="One sentence: what this page is for.")
    audience: str = Field(description="Who the page is written for.")
    primary_action: str | None = Field(
        description="The single most important thing a visitor should do here, if any."
    )
    primary_element: int | None = Field(
        description="Element number of the control for the primary action, if it exists."
    )
    site_language: str = Field(description="ISO 639-1 code of the page content.")


Viewport = Literal["desktop", "tablet", "mobile", "all"]
NoteCategory = Literal["visual", "ux", "content", "conversion", "accessibility"]
NoteSeverity = Literal["critical", "high", "medium", "low", "suggestion"]


class ReviewNote(BaseModel):
    element: int | None = Field(
        description="Element number from the element list, or null for a page-level note."
    )
    viewport: Viewport
    category: NoteCategory
    severity: NoteSeverity
    confidence: float = Field(description="0 to 1: how sure you are this is a real problem.")
    title: str
    description: str = Field(description="What is wrong and why it matters for this page.")
    recommendation: str = Field(description="A concrete change, with values where possible.")
    alternative: str | None = Field(
        description="An optional alternative layout or wording, or null."
    )
    evidence: str = Field(
        description="What in the screenshots or measurements shows this (image label, values)."
    )


class Scores(BaseModel):
    visual: int = Field(description="0-100")
    ux: int = Field(description="0-100")
    content: int = Field(description="0-100")
    conversion: int = Field(description="0-100")
    accessibility: int = Field(description="0-100")


class DesignReview(BaseModel):
    overall: str = Field(description="Two or three sentences summarising the page experience.")
    strengths: list[str]
    scores: Scores
    notes: list[ReviewNote]
