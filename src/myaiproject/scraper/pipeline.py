"""Composable data processing pipeline for scraped results."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import TYPE_CHECKING

from myaiproject.scraper.parser import ParsedPage

if TYPE_CHECKING:
    from myaiproject.scraper.summarizer import DeepSeekSummarizer

Processor = Callable[[ParsedPage], ParsedPage]


class Pipeline:
    """A chain of processing steps applied to each ParsedPage."""

    def __init__(self) -> None:
        self._steps: list[Processor] = []

    def add_step(self, processor: Processor) -> None:
        self._steps.append(processor)

    def run(self, pages: list[ParsedPage]) -> list[ParsedPage]:
        return [self._apply(page) for page in pages]

    def _apply(self, page: ParsedPage) -> ParsedPage:
        for step in self._steps:
            page = step(page)
        return page


def deduplicate_links(page: ParsedPage) -> ParsedPage:
    page.links = list(dict.fromkeys(page.links))
    return page


def strip_whitespace(page: ParsedPage) -> ParsedPage:
    page.text = re.sub(r"\s+", " ", page.text).strip()
    page.title = page.title.strip()
    return page


def create_summarize_step(
    summarizer: DeepSeekSummarizer,
) -> Processor:
    def _summarize(page: ParsedPage) -> ParsedPage:
        page.summary = summarizer.summarize(page.text)
        return page

    return _summarize


def filter_external_links(page: ParsedPage, domain: str) -> Processor:
    def _filter(page: ParsedPage) -> ParsedPage:
        from myaiproject.utils.url_utils import extract_domain

        page.links = [
            link
            for link in page.links
            if extract_domain(link) == domain
        ]
        return page

    return _filter
