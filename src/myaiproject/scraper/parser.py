"""HTML content parser built on BeautifulSoup + lxml."""

from __future__ import annotations

from dataclasses import dataclass, field

from bs4 import BeautifulSoup


@dataclass
class ParsedPage:
    """Structured data extracted from a single HTML page."""

    url: str
    title: str = ""
    text: str = ""
    summary: str = ""
    links: list[str] = field(default_factory=list)
    images: list[str] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)


class Parser:
    """Extracts data from HTML using CSS selectors."""

    def parse(self, html: str, url: str, selector: str | None = None) -> ParsedPage:
        """Parse HTML content and return structured data."""
        soup = BeautifulSoup(html, "lxml")
        result = ParsedPage(url=url)

        result.title = self._extract_title(soup)
        result.text = self._extract_text(soup, selector)
        result.links = self._extract_links(soup, url)
        result.images = self._extract_images(soup, url)
        result.metadata = self._extract_metadata(soup)

        return result

    @staticmethod
    def _extract_title(soup: BeautifulSoup) -> str:
        tag = soup.find("title")
        return tag.get_text(strip=True) if tag else ""

    @staticmethod
    def _extract_text(soup: BeautifulSoup, selector: str | None) -> str:
        if selector:
            elements = soup.select(selector)
            return "\n".join(e.get_text(" ", strip=True) for e in elements)
        body = soup.find("body")
        return body.get_text(" ", strip=True) if body else ""

    @staticmethod
    def _extract_links(soup: BeautifulSoup, base_url: str) -> list[str]:
        from urllib.parse import urljoin

        links: list[str] = []
        for a in soup.find_all("a", href=True):
            absolute = urljoin(base_url, str(a["href"]))
            links.append(absolute)
        return links

    @staticmethod
    def _extract_images(soup: BeautifulSoup, base_url: str) -> list[str]:
        from urllib.parse import urljoin

        images: list[str] = []
        for img in soup.find_all("img", src=True):
            absolute = urljoin(base_url, str(img["src"]))
            images.append(absolute)
        return images

    @staticmethod
    def _extract_metadata(soup: BeautifulSoup) -> dict[str, str]:
        meta: dict[str, str] = {}
        for tag in soup.find_all("meta"):
            name = tag.get("name") or tag.get("property")
            content = tag.get("content")
            if name and content:
                meta[str(name)] = str(content)
        return meta
