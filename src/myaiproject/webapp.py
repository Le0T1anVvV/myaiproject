"""Flask web interface for the AI-powered scraper."""

from __future__ import annotations

import asyncio
import os

from flask import Flask, Response, jsonify, render_template_string, request

from myaiproject.config import ScraperConfig, SummarizerConfig
from myaiproject.scraper.engine import ScraperEngine
from myaiproject.scraper.parser import ParsedPage
from myaiproject.scraper.pipeline import Pipeline, deduplicate_links, strip_whitespace

PAGE_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI 摘要抓取器</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    min-height: 100vh; padding: 20px;
  }
  .container { width: 100%; max-width: 720px; margin: 0 auto; }
  .card {
    background: #fff; border-radius: 16px; padding: 32px;
    box-shadow: 0 20px 60px rgba(0,0,0,.3); margin-bottom: 24px;
  }
  h1 { font-size: 1.5rem; color: #1a1a2e; margin-bottom: 8px; }
  .subtitle { color: #888; font-size: .85rem; margin-bottom: 24px; }
  .input-row { display: flex; flex-direction: column; gap: 10px; }
  .input-row textarea {
    width: 100%; padding: 12px 16px; border: 2px solid #e0e0e0;
    border-radius: 10px; font-size: .95rem; outline: none; resize: vertical;
    min-height: 100px; font-family: inherit;
    transition: border-color .2s;
  }
  .input-row textarea:focus { border-color: #302b63; }
  .input-row button {
    padding: 12px 24px; background: #302b63; color: #fff;
    border: none; border-radius: 10px; font-size: .95rem; cursor: pointer;
    font-weight: 600; transition: background .2s; align-self: flex-end;
  }
  .input-row button:hover { background: #24243e; }
  .input-row button:disabled { background: #aaa; cursor: not-allowed; }
  .loader {
    display: none; text-align: center; padding: 20px 0;
    color: #666; font-size: .9rem;
  }
  .loader.visible { display: block; }
  .spinner {
    display: inline-block; width: 24px; height: 24px;
    border: 3px solid #e0e0e0; border-top-color: #302b63;
    border-radius: 50%; animation: spin .8s linear infinite;
    vertical-align: middle; margin-right: 8px;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .results { display: none; }
  .results.visible { display: block; }
  .result-card {
    background: #f8f9ff; border-radius: 12px; padding: 20px;
    border-left: 4px solid #302b63; margin-bottom: 16px;
  }
  .result-card .title { font-size: 1.05rem; font-weight: 700; color: #1a1a2e; margin-bottom: 4px; word-break: break-all; }
  .result-card .url { font-size: .75rem; color: #aaa; margin-bottom: 10px; word-break: break-all; }
  .result-card .summary-label { font-size: .75rem; color: #302b63; font-weight: 700; text-transform: uppercase; letter-spacing: .5px; }
  .result-card .summary {
    font-size: .95rem; color: #333; line-height: 1.7; margin: 6px 0 10px;
    background: #fff; padding: 12px; border-radius: 8px;
  }
  .result-card .meta { font-size: .8rem; color: #999; display: flex; gap: 16px; }
  .result-card .meta span { background: #e8e8f0; padding: 2px 10px; border-radius: 20px; }
  .error {
    display: none; margin-top: 16px; padding: 12px 16px;
    background: #fff0f0; border-radius: 10px; color: #c0392b; font-size: .9rem;
  }
  .error.visible { display: block; }
</style>
</head>
<body>
<div class="container">
  <div class="card">
    <h1>AI 摘要抓取器</h1>
    <p class="subtitle">输入网页 URL（每行一个，支持批量），一键抓取并生成 AI 摘要（约100字）</p>
    <div class="input-row">
      <textarea id="urlInput" placeholder="https://example.com&#10;https://example.org&#10;https://example.net" autofocus></textarea>
      <button id="scrapeBtn" onclick="scrape()">批量抓取摘要</button>
    </div>
    <div class="loader" id="loader">
      <span class="spinner"></span>正在抓取并分析页面...
    </div>
    <div class="error" id="error"></div>
  </div>
  <div class="results" id="results"></div>
</div>
<script>
async function scrape() {
  const raw = document.getElementById('urlInput').value.trim();
  if (!raw) return;

  const urls = raw.split(/[\n,]+/).map(u => u.trim()).filter(u => u);
  if (!urls.length) return;

  const btn = document.getElementById('scrapeBtn');
  const loader = document.getElementById('loader');
  const error = document.getElementById('error');
  const results = document.getElementById('results');

  btn.disabled = true; loader.classList.add('visible');
  error.classList.remove('visible'); results.classList.remove('visible');
  results.innerHTML = '';

  try {
    const resp = await fetch('/api/scrape', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({urls})
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.error || 'Request failed');

    for (const page of data.pages) {
      const card = document.createElement('div');
      card.className = 'result-card';
      card.innerHTML =
        '<div class="title">' + escapeHtml(page.title || '(无标题)') + '</div>' +
        '<div class="url">' + escapeHtml(page.url) + '</div>' +
        '<div class="summary-label">AI 摘要</div>' +
        '<div class="summary">' + escapeHtml(page.summary || '(AI 摘要未生成)') + '</div>' +
        '<div class="meta">' +
          '<span>链接: ' + (page.links || 0) + '</span>' +
          '<span>图片: ' + (page.images || 0) + '</span>' +
        '</div>';
      results.appendChild(card);
    }
    results.classList.add('visible');
  } catch (e) {
    error.textContent = e.message; error.classList.add('visible');
  } finally {
    btn.disabled = false; loader.classList.remove('visible');
  }
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

document.getElementById('urlInput').addEventListener('keydown', function(e) {
  if (e.key === 'Enter' && e.ctrlKey) scrape();
});
</script>
</body>
</html>"""


def create_app(*, debug: bool = False) -> Flask:
    app = Flask(__name__)
    app.config["DEBUG"] = debug

    @app.route("/")
    def index() -> str:
        return render_template_string(PAGE_HTML)

    @app.route("/api/scrape", methods=["POST"])
    def api_scrape() -> tuple[Response, int] | Response:
        data = request.get_json(silent=True) or {}
        raw_urls: list[str] = data.get("urls") or []
        if not raw_urls:
            return jsonify({"error": "URLs are required"}), 400

        urls = [u.strip() for u in raw_urls if u.strip()]
        if not urls:
            return jsonify({"error": "URLs are required"}), 400

        enabled = bool(os.getenv("DEEPSEEK_API_KEY"))
        config = ScraperConfig(
            output_dir="output",
            output_format="json",
            summarizer=SummarizerConfig(enabled=enabled),
        )
        pipeline = Pipeline()
        pipeline.add_step(strip_whitespace)
        pipeline.add_step(deduplicate_links)

        engine = ScraperEngine(config, pipeline)

        async def _run() -> list[ParsedPage]:
            return await engine.run(urls)

        pages = asyncio.run(_run())

        results = []
        for page in pages:
            results.append({
                "url": page.url,
                "title": page.title,
                "summary": page.summary,
                "text": page.text[:500],
                "links": len(page.links),
                "images": len(page.images),
            })

        return jsonify({"pages": results})

    return app
