"""Tests for the Flask web application."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from pytest_httpx import HTTPXMock

from myaiproject.webapp import create_app


@pytest.fixture(autouse=True)
def _clear_api_key():
    """Ensure DEEPSEEK_API_KEY is unset so summarizer stays off by default."""
    with patch.dict(os.environ, {}, clear=True):
        yield


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_index_returns_html(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"<!DOCTYPE html>" in resp.data
    assert b"AI" in resp.data


def test_api_scrape_requires_url(client):
    resp = client.post("/api/scrape", json={})
    assert resp.status_code == 400
    data = resp.get_json()
    assert "URL" in data["error"]


def test_api_scrape_succeeds(client, httpx_mock: HTTPXMock):
    url = "https://example.com"
    httpx_mock.add_response(
        url=url,
        text="<html><head><title>Test</title></head><body><p>Hello</p></body></html>",
    )

    resp = client.post("/api/scrape", json={"url": url})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["title"] == "Test"
    assert data["links"] == 0
    assert data["images"] == 0


def test_api_scrape_handles_bad_url(client, httpx_mock: HTTPXMock):
    url = "https://bad.example"
    httpx_mock.add_exception(url=url, exception=Exception("Connection failed"))

    resp = client.post("/api/scrape", json={"url": url})
    assert resp.status_code == 500
    data = resp.get_json()
    assert "Error" in data["error"]


def test_api_scrape_returns_summary_when_enabled(
    client, httpx_mock: HTTPXMock
):
    url = "https://example.com"
    httpx_mock.add_response(
        url=url,
        text="<html><head><title>T</title></head><body>text</body></html>",
    )
    httpx_mock.add_response(
        url="https://api.deepseek.com/chat/completions",
        json={
            "choices": [{"message": {"content": "a summary"}}]
        },
    )

    with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "sk-test"}):
        resp = client.post("/api/scrape", json={"url": url})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["summary"] == "a summary"
