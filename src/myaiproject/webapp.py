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
    min-height: 100vh; display: flex; align-items: center; justify-content: center;
    padding: 20px;
  }
  .container { width: 100%; max-width: 640px; }
  .card {
    background: #fff; border-radius: 16px; padding: 32px;
    box-shadow: 0 20px 60px rgba(0,0,0,.3);
  }
  h1 { font-size: 1.5rem; color: #1a1a2e; margin-bottom: 8px; }
  .subtitle { color: #888; font-size: .85rem; margin-bottom: 24px; }
  .input-row { display: flex; gap: 10px; }
  .input-row input {
    flex: 1; padding: 12px 16px; border: 2px solid #e0e0e0;
    border-radius: 10px; font-size: .95rem; outline: none;
    transition: border-color .2s;
  }
  .input-row input:focus { border-color: #302b63; }
  .input-row button {
    padding: 12px 24px; background: #302b63; color: #fff;
    border: none; border-radius: 10px; font-size: .95rem; cursor: pointer;
    font-weight: 600; white-space: nowrap; transition: background .2s;
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
  .result { display: none; margin-top: 24px; }
  .result.visible { display: block; }
  .result-card {
    background: #f8f9ff; border-radius: 12px; padding: 20px;
    border-left: 4px solid #302b63;
  }
  .result-card .title { font-size: 1.1rem; font-weight: 700; color: #1a1a2e; margin-bottom: 12px; }
  .result-card .summary-label { font-size: .75rem; color: #302b63; font-weight: 700; text-transform: uppercase; letter-spacing: .5px; }
  .result-card .summary {
    font-size: 1rem; color: #333; line-height: 1.6; margin: 6px 0 14px;
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
    <p class="subtitle">输入任意网页 URL，一键抓取并生成 AI 摘要</p>
    <div class="input-row">
      <input type="url" id="urlInput" placeholder="https://example.com" autofocus>
      <button id="scrapeBtn" onclick="scrape()">抓取摘要</button>
    </div>
    <div class="loader" id="loader">
      <span class="spinner"></span>正在抓取并分析页面...
    </div>
    <div class="error" id="error"></div>
    <div class="result" id="result">
      <div class="result-card">
        <div class="title" id="resultTitle"></div>
        <div class="summary-label">AI 摘要</div>
        <div class="summary" id="resultSummary"></div>
        <div class="meta">
          <span id="resultLinks"></span>
          <span id="resultImages"></span>
          <span id="resultTime"></span>
        </div>
      </div>
    </div>
  </div>
</div>
<script>
async function scrape() {
  const url = document.getElementById('urlInput').value.trim();
  if (!url) return;

  const btn = document.getElementById('scrapeBtn');
  const loader = document.getElementById('loader');
  const error = document.getElementById('error');
  const result = document.getElementById('result');

  btn.disabled = true; loader.classList.add('visible');
  error.classList.remove('visible'); result.classList.remove('visible');

  try {
    const resp = await fetch('/api/scrape', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({url})
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.error || 'Request failed');

    document.getElementById('resultTitle').textContent = data.title || '(无标题)';
    document.getElementById('resultSummary').textContent = data.summary || '(AI 摘要未生成 — 请确保已设置 DEEPSEEK_API_KEY)';
    document.getElementById('resultLinks').textContent = '链接: ' + (data.links || 0);
    document.getElementById('resultImages').textContent = '图片: ' + (data.images || 0);
    document.getElementById('resultTime').textContent = (data.elapsed || 0).toFixed(1) + 's';
    result.classList.add('visible');
  } catch (e) {
    error.textContent = e.message; error.classList.add('visible');
  } finally {
    btn.disabled = false; loader.classList.remove('visible');
  }
}
document.getElementById('urlInput').addEventListener('keydown', function(e) {
  if (e.key === 'Enter') scrape();
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
        url = (data.get("url") or "").strip()
        if not url:
            return jsonify({"error": "URL is required"}), 400

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
            return await engine.run([url])

        pages = asyncio.run(_run())

        if not pages:
            return jsonify({"error": "Failed to scrape"}), 500

        page = pages[0]
        if page.text.startswith("Error:"):
            return jsonify({"error": page.text}), 500

        return jsonify({
            "url": page.url,
            "title": page.title,
            "summary": page.summary,
            "text": page.text[:500],
            "links": len(page.links),
            "images": len(page.images),
            "elapsed": 0,
        })

    return app
