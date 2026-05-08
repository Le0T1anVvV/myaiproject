"""Core scraping engine that orchestrates fetch → parse → pipeline → export."""

from __future__ import annotations

import asyncio

from myaiproject.config import ScraperConfig
from myaiproject.scraper.exporter import Exporter
from myaiproject.scraper.fetcher import Fetcher
from myaiproject.scraper.parser import ParsedPage, Parser
from myaiproject.scraper.pipeline import Pipeline


class ScraperEngine:
    """Orchestrates the full scraping workflow for a list of URLs."""

    def __init__(
        self, config: ScraperConfig, pipeline: Pipeline | None = None
    ) -> None:
        self._config = config
        self._pipeline = pipeline or Pipeline()
        if config.summarizer.is_ready:
            from myaiproject.scraper.pipeline import create_summarize_step
            from myaiproject.scraper.summarizer import DeepSeekSummarizer

            summarizer = DeepSeekSummarizer(config.summarizer)
            self._pipeline.add_step(create_summarize_step(summarizer))

    async def run(
        self, urls: list[str], selector: str | None = None
    ) -> list[ParsedPage]:
        """Scrape multiple URLs concurrently up to *max_concurrency*."""
        semaphore = asyncio.Semaphore(self._config.max_concurrency)
        fetcher = Fetcher(self._config)
        parser = Parser()

        async def scrape_one(url: str) -> ParsedPage:
            async with semaphore:
                result = await fetcher.fetch(url)
                return parser.parse(result.content, result.url, selector)

        try:
            results = await asyncio.gather(
                *(scrape_one(url) for url in urls),
                return_exceptions=True,
            )
        finally:
            await fetcher.close()

        pages: list[ParsedPage] = []
        for item, url in zip(results, urls):
            if isinstance(item, BaseException):
                pages.append(ParsedPage(url=url, text=f"Error: {item}"))
            else:
                pages.append(item)

        pages = self._pipeline.run(pages)
        return pages

    def export(self, pages: list[ParsedPage]) -> list[str]:
        """Export results and return the output file paths."""
        exporter = Exporter(self._config.output_dir)
        paths = exporter.export(pages, self._config.output_format)
        return [str(p) for p in paths]
