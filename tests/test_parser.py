"""Tests for the HTML parser."""

from __future__ import annotations

from myaiproject.scraper.parser import ParsedPage, Parser


def test_parser_extracts_title(sample_html, sample_url):
    parser = Parser()
    result = parser.parse(sample_html, sample_url)
    assert result.title == "Test Page"


def test_parser_extracts_links(sample_html, sample_url):
    parser = Parser()
    result = parser.parse(sample_html, sample_url)
    assert len(result.links) == 2
    assert result.links[0].endswith("/page2")
    assert result.links[1] == "https://example.com/page3"


def test_parser_extracts_images(sample_html, sample_url):
    parser = Parser()
    result = parser.parse(sample_html, sample_url)
    assert len(result.images) == 2


def test_parser_extracts_metadata(sample_html, sample_url):
    parser = Parser()
    result = parser.parse(sample_html, sample_url)
    assert result.metadata["description"] == "A test page"


def test_parser_respects_css_selector(sample_html, sample_url):
    parser = Parser()
    result = parser.parse(sample_html, sample_url, selector="h1")
    assert result.text.strip() == "Hello World"


def test_parser_handles_empty_html(sample_url):
    parser = Parser()
    result = parser.parse("", sample_url)
    assert isinstance(result, ParsedPage)
    assert result.title == ""
    assert result.links == []


def test_parser_handles_no_title(sample_url):
    parser = Parser()
    result = parser.parse("<html><body>no title</body></html>", sample_url)
    assert result.title == ""
    assert "no title" in result.text
