from dataclasses import dataclass, field
from urllib.parse import urljoin
from xml.etree.ElementTree import Element

from defusedxml import DefusedXmlException
from defusedxml.ElementTree import ParseError, fromstring


@dataclass
class SitemapEntries:
    pages: list[str] = field(default_factory=list)
    sitemaps: list[str] = field(default_factory=list)


def parse_sitemap(content: bytes, source_url: str) -> SitemapEntries:
    try:
        root = fromstring(content)
    except (ParseError, DefusedXmlException):
        return SitemapEntries()

    kind = _local(root)
    locations = [
        urljoin(source_url, loc.text.strip())
        for loc in root.iter()
        if _local(loc) == "loc" and loc.text and loc.text.strip()
    ]
    if kind == "urlset":
        return SitemapEntries(pages=locations)
    if kind == "sitemapindex":
        return SitemapEntries(sitemaps=locations)
    return SitemapEntries()


def parse_robots(content: str, source_url: str) -> list[str]:
    found = []
    for line in content.splitlines():
        key, _, value = line.partition(":")
        if key.strip().lower() == "sitemap" and value.strip():
            found.append(urljoin(source_url, value.strip()))
    return found


def _local(element: Element) -> str:
    return element.tag.rsplit("}", 1)[-1]
