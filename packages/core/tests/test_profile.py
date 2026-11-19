import pytest
from pydantic import ValidationError

from clarity_core.domain.profile import AnalysisProfile, Language, ScopeMode
from clarity_core.domain.viewport import Viewport


def test_defaults_cover_whole_site_on_desktop_and_mobile() -> None:
    profile = AnalysisProfile(start_url="theqiyas.cc")
    assert profile.start_url == "https://theqiyas.cc/"
    assert profile.scope is ScopeMode.SITE
    assert profile.viewports == [Viewport.DESKTOP, Viewport.MOBILE]
    assert profile.language is Language.EN


def test_selected_pages_must_belong_to_the_site() -> None:
    with pytest.raises(ValidationError, match="outside"):
        AnalysisProfile(
            start_url="https://theqiyas.cc",
            scope=ScopeMode.PAGES,
            pages=["https://other.example/about"],
        )


def test_selected_pages_are_normalized() -> None:
    profile = AnalysisProfile(
        start_url="https://theqiyas.cc",
        scope=ScopeMode.PAGES,
        pages=["https://www.theqiyas.cc/listings#top"],
    )
    assert profile.pages == ["https://www.theqiyas.cc/listings"]


def test_pages_scope_requires_pages() -> None:
    with pytest.raises(ValidationError, match="at least one page"):
        AnalysisProfile(start_url="https://theqiyas.cc", scope=ScopeMode.PAGES)


def test_single_page_scope_limits_crawl() -> None:
    profile = AnalysisProfile(start_url="https://theqiyas.cc/listing/1", scope=ScopeMode.SINGLE)
    assert profile.limits.max_pages == 1
    assert profile.limits.max_depth == 0


def test_viewports_are_deduplicated() -> None:
    profile = AnalysisProfile(
        start_url="https://theqiyas.cc", viewports=[Viewport.MOBILE, Viewport.MOBILE]
    )
    assert profile.viewports == [Viewport.MOBILE]


def test_viewport_dimensions() -> None:
    assert (Viewport.MOBILE.width, Viewport.MOBILE.height) == (390, 844)
    assert Viewport.MOBILE.is_mobile
    assert not Viewport.DESKTOP.is_mobile
