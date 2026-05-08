"""Tests for the scraping engine."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from pytest_httpx import HTTPXMock


@pytest.mark.asyncio
async def test_engine_scrapes_and_exports(sample_config, httpx_mock: HTTPXMock):
    from myaiproject.scraper.engine import ScraperEngine

    url = "https://example.com"
    httpx_mock.add_response(
        url=url,
        text="<html><head><title>Test</title></head><body><p>content</p></body></html>",
    )

    engine = ScraperEngine(sample_config)
    pages = await engine.run([url])
    paths = engine.export(pages)

    assert len(pages) == 1
    assert pages[0].title == "Test"
    assert len(paths) == 1
    assert Path(paths[0]).exists()

    data = json.loads(Path(paths[0]).read_text(encoding="utf-8"))
    assert data[0]["title"] == "Test"

    # Cleanup
    shutil.rmtree(sample_config.output_dir, ignore_errors=True)


@pytest.mark.asyncio
async def test_engine_handles_errors_gracefully(sample_config):
    from myaiproject.scraper.engine import ScraperEngine

    engine = ScraperEngine(sample_config)
    pages = await engine.run(["not-a-valid-url"])

    assert len(pages) == 1
    assert "Error" in pages[0].text


@pytest.mark.asyncio
async def test_engine_with_css_selector(sample_config, httpx_mock: HTTPXMock):
    from myaiproject.scraper.engine import ScraperEngine

    url = "https://example.com"
    httpx_mock.add_response(
        url=url,
        text="<html><body><h1>Heading</h1><p>Body text</p></body></html>",
    )

    engine = ScraperEngine(sample_config)
    pages = await engine.run([url], selector="h1")
    assert pages[0].text.strip() == "Heading"
