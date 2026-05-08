# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build / Test / Lint

```bash
pip install -e ".[dev]"          # Install project + dev dependencies
pytest -v                        # Run all tests
pytest -v tests/test_parser.py   # Run a single test file
pytest -v -k "test_engine"       # Run tests matching a keyword
ruff check src/                  # Lint source code
ruff check --fix src/            # Auto-fix lint issues
mypy src/                        # Type check
python -m myaiproject scrape <url>  # Run the scraper CLI
python -m myaiproject scrape <url> --summarize  # Scrape + DeepSeek summary
```

## Style Guide

Follow the **Google Python Style Guide**. Key points:
- `from __future__ import annotations` in every file
- Functions and methods: `lower_with_underscores`
- Classes and types: `CapWords`
- Modules: `lower_with_underscores.py`
- Docstrings: one-line summary, no multi-paragraph prose unless the WHY is non-obvious
- Imports: stdlib → third-party → first-party, each group separated by a blank line
- Prefer `dataclass` over plain dicts for structured data; use `pydantic` at external boundaries

## Architecture

```
src/myaiproject/
├── __init__.py       # Package version
├── __main__.py       # Entry: python -m myaiproject
├── cli.py            # argparse CLI (scrape subcommand)
├── config.py         # ScraperConfig dataclass — all tunables live here
├── scraper/
│   ├── engine.py     # ScraperEngine — orchestrates the pipeline via asyncio.gather
│   ├── fetcher.py    # Fetcher — httpx.AsyncClient + tenacity retry + rate limiting
│   ├── parser.py     # Parser — BeautifulSoup/lxml, returns ParsedPage dataclass
│   ├── pipeline.py   # Pipeline — composable callables (Processor = Callable[[ParsedPage], ParsedPage])
│   ├── exporter.py   # Exporter — writes ParsedPage list to JSON or CSV
│   └── summarizer.py # DeepSeekSummarizer — calls DeepSeek API for text summarization
└── utils/
    └── url_utils.py  # URL normalization, domain extraction, validation
```

**Data flow:** `CLI args → ScraperConfig → ScraperEngine.run(urls) → Fetcher.fetch() → Parser.parse() → Pipeline.run() → Exporter.export()`

Each `Fetcher` owns a single `httpx.AsyncClient` and must be `.close()`'d after use (`ScraperEngine` handles this in a `finally` block). Concurrency is controlled by `asyncio.Semaphore(max_concurrency)`. The `Pipeline` is a list of `Processor` callables applied in order — add steps via `pipeline.add_step(func)`.

Built-in pipeline steps: `strip_whitespace`, `deduplicate_links`, `filter_external_links(domain)`, `create_summarize_step(summarizer)`.

## DeepSeek Summarizer

Enable with `--summarize` flag (requires `DEEPSEEK_API_KEY` environment variable):

```bash
$env:DEEPSEEK_API_KEY = "sk-xxx"
python -m myaiproject scrape https://example.com --summarize
```

`DeepSeekSummarizer` uses the OpenAI-compatible SDK (`base_url=https://api.deepseek.com`, model=`deepseek-chat`). If the API call fails, an empty string is returned with a warning log — scraping continues uninterrupted. Configuration in `SummarizerConfig` (inside `config.py`): `api_key`, `base_url`, `model`, `max_tokens`, `enabled`.

## Testing

Tests live in `tests/` and use `pytest` with `pytest-httpx` for mocking HTTP responses. `asyncio_mode = "auto"` is configured so `pytest.mark.asyncio` is required only when the test function itself is async. Shared fixtures (`sample_config`, `sample_html`, `sample_url`) are in `conftest.py`.

When adding tests for a new module, mock at the HTTP boundary with `pytest-httpx`, not at the internal module boundary.
