"""Shared fixtures for scraper tests."""

from __future__ import annotations

import pytest

from myaiproject.config import ScraperConfig


@pytest.fixture
def sample_config() -> ScraperConfig:
    return ScraperConfig(
        timeout=5.0,
        max_retries=1,
        rate_limit=0.0,
        max_concurrency=1,
        output_dir="tests/output",
        output_format="json",
    )


@pytest.fixture
def sample_html() -> str:
    return """\
<html>
<head>
<title>Test Page</title>
<meta name="description" content="A test page">
</head>
<body>
<h1>Hello World</h1>
<p>This is a test paragraph.</p>
<a href="/page2">Page 2</a>
<a href="https://example.com/page3">Page 3</a>
<img src="/img/photo.jpg">
<img src="https://cdn.example.com/banner.png">
</body>
</html>"""


@pytest.fixture
def sample_url() -> str:
    return "https://example.com/test"
