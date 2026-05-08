"""DeepSeek-powered text summarizer using OpenAI-compatible API."""

from __future__ import annotations

import logging

from openai import OpenAI

from myaiproject.config import SummarizerConfig

logger = logging.getLogger(__name__)

_SUMMARIZE_PROMPT = "请用50字以内总结以下内容的核心要点："
_MAX_INPUT_CHARS = 3000


class DeepSeekSummarizer:
    """Calls the DeepSeek API to summarize text."""

    def __init__(self, config: SummarizerConfig) -> None:
        self._config = config
        self._client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
        )

    def summarize(self, text: str) -> str:
        """Return a short summary of *text*, or an empty string on failure."""
        if not text.strip():
            return ""

        truncated = text[:_MAX_INPUT_CHARS]
        try:
            response = self._client.chat.completions.create(
                model=self._config.model,
                messages=[
                    {"role": "user", "content": f"{_SUMMARIZE_PROMPT}\n\n{truncated}"}
                ],
                max_tokens=self._config.max_tokens,
                temperature=0.3,
            )
            content = response.choices[0].message.content
            return content.strip() if content else ""
        except Exception:
            logger.warning("DeepSeek summarization failed", exc_info=True)
            return ""
