from clarity_worker.sitemap import parse_robots, parse_sitemap

URLSET = b"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://shop.test/</loc></url>
  <url><loc> /about </loc></url>
</urlset>"""

INDEX = b"""<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://shop.test/sitemap-pages.xml</loc></sitemap>
</sitemapindex>"""


def test_urlset_resolves_relative_locations() -> None:
    result = parse_sitemap(URLSET, "https://shop.test/sitemap.xml")
    assert result.pages == ["https://shop.test/", "https://shop.test/about"]
    assert result.sitemaps == []


def test_index_lists_child_sitemaps() -> None:
    result = parse_sitemap(INDEX, "https://shop.test/sitemap.xml")
    assert result.sitemaps == ["https://shop.test/sitemap-pages.xml"]


def test_garbage_is_empty() -> None:
    result = parse_sitemap(b"<html>not a sitemap", "https://shop.test/sitemap.xml")
    assert result.pages == []
    assert result.sitemaps == []


def test_entities_are_not_expanded() -> None:
    bomb = b"""<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "aaaa">]>
    <urlset><url><loc>&a;</loc></url></urlset>"""
    assert parse_sitemap(bomb, "https://shop.test/sitemap.xml").pages == []


def test_robots_sitemap_lines() -> None:
    robots = "User-agent: *\nDisallow: /admin\nSitemap: https://shop.test/sm.xml\nsitemap: /b.xml\n"
    assert parse_robots(robots, "https://shop.test/robots.txt") == [
        "https://shop.test/sm.xml",
        "https://shop.test/b.xml",
    ]
