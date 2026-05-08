"""Tests for the data processing pipeline."""

from __future__ import annotations

from myaiproject.scraper.parser import ParsedPage
from myaiproject.scraper.pipeline import (
    Pipeline,
    deduplicate_links,
    filter_external_links,
    strip_whitespace,
)


def _make_page(**kwargs) -> ParsedPage:
    defaults = {
        "url": "https://example.com",
        "title": "Title  ",
        "text": "  hello   world  ",
        "links": [
            "https://example.com/a",
            "https://example.com/a",
            "https://other.com/b",
        ],
        "images": [],
        "metadata": {},
    }
    defaults.update(kwargs)
    return ParsedPage(**defaults)


def test_strip_whitespace():
    page = _make_page()
    result = strip_whitespace(page)
    assert result.title == "Title"
    assert result.text == "hello world"


def test_deduplicate_links():
    page = _make_page()
    result = deduplicate_links(page)
    assert len(result.links) == 2


def test_filter_external_links():
    page = _make_page()
    step = filter_external_links(page, "example.com")
    result = step(page)
    assert all("example.com" in link for link in result.links)
    assert len(result.links) == 2


def test_pipeline_runs_all_steps():
    page = _make_page()
    pipeline = Pipeline()
    pipeline.add_step(strip_whitespace)
    pipeline.add_step(deduplicate_links)
    pipeline.add_step(filter_external_links(page, "example.com"))

    results = pipeline.run([page])
    assert results[0].title == "Title"
    assert results[0].text == "hello world"
    assert results[0].links == ["https://example.com/a"]
