"""Tests for the DeepSeek summarizer."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from myaiproject.config import SummarizerConfig
from myaiproject.scraper.summarizer import DeepSeekSummarizer


@pytest.fixture
def summarizer_config() -> SummarizerConfig:
    return SummarizerConfig(
        api_key="sk-test-key",
        base_url="https://api.deepseek.com",
        model="deepseek-chat",
        max_tokens=100,
        enabled=True,
    )


def test_summarizer_returns_summary(summarizer_config):
    with patch("myaiproject.scraper.summarizer.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content="这是一个测试摘要。"))
        ]
        mock_client.chat.completions.create.return_value = mock_completion
        mock_openai.return_value = mock_client

        summarizer = DeepSeekSummarizer(summarizer_config)
        result = summarizer.summarize("这是一段很长的测试文本。" * 100)

        assert result == "这是一个测试摘要。"
        mock_client.chat.completions.create.assert_called_once()


def test_summarizer_handles_empty_text(summarizer_config):
    summarizer = DeepSeekSummarizer(summarizer_config)
    result = summarizer.summarize("")
    assert result == ""


def test_summarizer_handles_api_error(summarizer_config):
    with patch("myaiproject.scraper.summarizer.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API error")
        mock_openai.return_value = mock_client

        summarizer = DeepSeekSummarizer(summarizer_config)
        result = summarizer.summarize("test text")

        assert result == ""


def test_summarizer_truncates_long_text(summarizer_config):
    with patch("myaiproject.scraper.summarizer.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content="summarized"))
        ]
        mock_client.chat.completions.create.return_value = mock_completion
        mock_openai.return_value = mock_client

        long_text = "x" * 5000
        summarizer = DeepSeekSummarizer(summarizer_config)
        summarizer.summarize(long_text)

        call_args = mock_client.chat.completions.create.call_args
        sent_text = call_args[1]["messages"][0]["content"]
        assert len(sent_text) < len(long_text)
        assert len(sent_text) <= 3000 + 100  # prompt + truncated text


def test_config_is_ready():
    ready = SummarizerConfig(api_key="sk-xxx", enabled=True)
    assert ready.is_ready

    no_key = SummarizerConfig(api_key="", enabled=True)
    assert not no_key.is_ready

    not_enabled = SummarizerConfig(api_key="sk-xxx", enabled=False)
    assert not not_enabled.is_ready
