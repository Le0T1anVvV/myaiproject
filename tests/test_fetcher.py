"""Tests for the async HTTP fetcher."""

from __future__ import annotations

import pytest
from pytest_httpx import HTTPXMock

from myaiproject.scraper.fetcher import Fetcher, FetchResult


@pytest.mark.asyncio
async def test_fetcher_returns_fetch_result(
    sample_config, httpx_mock: HTTPXMock
):
    url = "https://example.com"
    httpx_mock.add_response(url=url, text="<html></html>", status_code=200)

    fetcher = Fetcher(sample_config)
    result = await fetcher.fetch(url)
    await fetcher.close()

    assert isinstance(result, FetchResult)
    assert result.status_code == 200
    assert result.url == url
    assert "<html>" in result.content


@pytest.mark.asyncio
async def test_fetcher_retries_on_failure(
    sample_config, httpx_mock: HTTPXMock
):
    url = "https://example.com"
    # First response returns 500 (triggers retry), second returns 200.
    httpx_mock.add_response(url=url, status_code=500)
    httpx_mock.add_response(url=url, text="ok", status_code=200)

    sample_config.max_retries = 2
    fetcher = Fetcher(sample_config)
    result = await fetcher.fetch(url)
    await fetcher.close()

    assert result.status_code == 200


@pytest.mark.asyncio
async def test_fetcher_respects_rate_limit(
    sample_config, httpx_mock: HTTPXMock
):
    url = "https://example.com"
    httpx_mock.add_response(url=url, text="<html></html>", is_reusable=True)

    sample_config.rate_limit = 0.2
    fetcher = Fetcher(sample_config)
    await fetcher.fetch(url)
    await fetcher.fetch(url)
    await fetcher.close()


@pytest.mark.asyncio
async def test_fetcher_timeout_propagates(sample_config):
    url = "https://example.com"
    sample_config.max_retries = 1
    sample_config.timeout = 0.001
    fetcher = Fetcher(sample_config)

    with pytest.raises(Exception):
        await fetcher.fetch(url)
    await fetcher.close()
