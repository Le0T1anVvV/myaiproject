"""Command-line interface for the web scraper."""

from __future__ import annotations

import argparse
import asyncio

from myaiproject.config import ScraperConfig
from myaiproject.scraper.engine import ScraperEngine
from myaiproject.scraper.pipeline import (
    Pipeline,
    deduplicate_links,
    strip_whitespace,
)


def main() -> None:
    parser = argparse.ArgumentParser(prog="myaiproject")
    subparsers = parser.add_subparsers(dest="command", required=True)

    _add_scrape_parser(subparsers)
    args = parser.parse_args()
    asyncio.run(_handle_scrape(args))


def _add_scrape_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    scrape = subparsers.add_parser("scrape", help="Scrape one or more URLs")
    scrape.add_argument("urls", nargs="+", help="URL(s) to scrape")
    scrape.add_argument(
        "--output", choices=["json", "csv"], default="json",
        help="Output format (default: json)"
    )
    scrape.add_argument(
        "--output-dir", default="output",
        help="Output directory (default: output)"
    )
    scrape.add_argument(
        "--selector", default=None,
        help="CSS selector to extract specific content"
    )
    scrape.add_argument(
        "--concurrency", type=int, default=5,
        help="Max concurrent requests (default: 5)"
    )
    scrape.add_argument(
        "--rate-limit", type=float, default=1.0,
        help="Seconds between requests per worker (default: 1.0)"
    )
    scrape.add_argument(
        "--timeout", type=float, default=30.0,
        help="Request timeout in seconds (default: 30)"
    )
    scrape.add_argument(
        "--max-retries", type=int, default=3,
        help="Max retry attempts on failure (default: 3)"
    )
    scrape.add_argument(
        "--summarize", action="store_true", default=False,
        help="Summarize page text via DeepSeek API (requires DEEPSEEK_API_KEY)"
    )


async def _handle_scrape(args: argparse.Namespace) -> None:
    from myaiproject.config import SummarizerConfig

    config = ScraperConfig(
        output_format=args.output,
        output_dir=args.output_dir,
        max_concurrency=args.concurrency,
        rate_limit=args.rate_limit,
        timeout=args.timeout,
        max_retries=args.max_retries,
        summarizer=SummarizerConfig(enabled=args.summarize),
    )

    pipeline = Pipeline()
    pipeline.add_step(strip_whitespace)
    pipeline.add_step(deduplicate_links)

    engine = ScraperEngine(config, pipeline)
    pages = await engine.run(args.urls, selector=args.selector)
    paths = engine.export(pages)

    print(f"Scraped {len(pages)} page(s). Output written to:")
    for p in paths:
        print(f"  {p}")


if __name__ == "__main__":
    main()
