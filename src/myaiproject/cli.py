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
    _add_web_parser(subparsers)
    args = parser.parse_args()
    _dispatch(args)


def _dispatch(args: argparse.Namespace) -> None:
    if args.command == "scrape":
        asyncio.run(_handle_scrape(args))
    elif args.command == "web":
        _handle_web(args)


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


def _add_web_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    web = subparsers.add_parser("web", help="Start the web UI server")
    web.add_argument(
        "--port", type=int, default=0,
        help="Server port (default: 5000 dev, $PORT in production)"
    )
    web.add_argument(
        "--host", default="127.0.0.1",
        help="Server host (default: 127.0.0.1, 0.0.0.0 in production)"
    )
    web.add_argument(
        "--production", action="store_true", default=False,
        help="Run with waitress WSGI server for production"
    )


def _handle_web(args: argparse.Namespace) -> None:
    import os

    from myaiproject.webapp import create_app

    if args.production:
        from waitress import serve

        port = args.port or int(os.getenv("PORT", "5000"))
        host = "0.0.0.0"
        print(f"\n  Production server on http://0.0.0.0:{port}\n")
        serve(create_app(debug=False), host=host, port=port)
    else:
        port = args.port or 5000
        app = create_app(debug=True)
        print(f"\n  Web UI: http://{args.host}:{port}\n")
        app.run(host=args.host, port=port, debug=True)


if __name__ == "__main__":
    main()
