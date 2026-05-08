"""Configuration for the scraper, loadable from JSON or kwargs."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_USER_AGENT = (
    "MyAIProject-Scraper/0.1 (compatible; +https://github.com/example)"
)


@dataclass
class SummarizerConfig:
    """Configuration for the DeepSeek-powered summarizer."""

    api_key: str = field(
        default_factory=lambda: os.getenv("DEEPSEEK_API_KEY", "")
    )
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-chat"
    max_tokens: int = 200
    enabled: bool = False

    @property
    def is_ready(self) -> bool:
        """Return True if the API key is set and summarization is enabled."""
        return self.enabled and bool(self.api_key)


@dataclass
class ScraperConfig:
    """Configuration for the scraping engine."""

    timeout: float = 30.0
    user_agent: str = DEFAULT_USER_AGENT
    max_retries: int = 3
    rate_limit: float = 1.0
    max_concurrency: int = 5
    output_dir: str = "output"
    output_format: str = "json"
    request_headers: dict[str, str] = field(default_factory=dict)
    follow_redirects: bool = True
    summarizer: SummarizerConfig = field(default_factory=SummarizerConfig)

    @classmethod
    def from_file(cls, path: str | Path) -> ScraperConfig:
        """Load configuration from a JSON file."""
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_dict(raw)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ScraperConfig:
        """Create a config from a dictionary of known keys."""
        valid_keys = {f.name for f in dataclass_fields(cls)}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


def dataclass_fields(cls: type[Any]) -> tuple[Any, ...]:
    """Backport of dataclasses.fields for runtime inspection."""
    from dataclasses import fields as _fields

    return _fields(cls)
