"""Async HTTP fetcher with retry logic and rate limiting."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from myaiproject.config import ScraperConfig

_RETRYABLE = (
    httpx.TimeoutException,
    httpx.ConnectError,
    httpx.RemoteProtocolError,
    httpx.HTTPStatusError,
)


@dataclass
class FetchResult:
    """Result of a single page fetch."""

    url: str
    status_code: int
    content: str
    headers: httpx.Headers
    elapsed: float


class Fetcher:
    """Async HTTP fetcher with configurable retry and rate limiting."""

    def __init__(self, config: ScraperConfig) -> None:
        self._config = config
        self._last_request_time = 0.0
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(config.timeout),
            headers={"User-Agent": config.user_agent, **config.request_headers},
            follow_redirects=config.follow_redirects,
        )

    async def fetch(self, url: str) -> FetchResult:
        """Fetch a single URL, respecting rate limits and retrying on failure."""
        await self._throttle()
        start = time.monotonic()
        response = await self._request_with_retry(url)
        elapsed = time.monotonic() - start
        return FetchResult(
            url=str(response.url),
            status_code=response.status_code,
            content=response.text,
            headers=response.headers,
            elapsed=elapsed,
        )

    async def _request_with_retry(self, url: str) -> httpx.Response:
        @retry(
            stop=stop_after_attempt(self._config.max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type(_RETRYABLE),
        )
        async def _do() -> httpx.Response:
            response = await self._client.get(url)
            if response.status_code >= 500:
                response.raise_for_status()
            return response

        return await _do()

    async def _throttle(self) -> None:
        """Enforce the configured rate limit between requests."""
        elapsed = time.monotonic() - self._last_request_time
        wait = self._config.rate_limit - elapsed
        if wait > 0:
            await asyncio.sleep(wait)
        self._last_request_time = time.monotonic()

    async def close(self) -> None:
        await self._client.aclose()
