"""Example: basic single-page scrape using the engine."""

import asyncio

from myaiproject.config import ScraperConfig
from myaiproject.scraper.engine import ScraperEngine
from myaiproject.scraper.pipeline import (
    Pipeline,
    deduplicate_links,
    strip_whitespace,
)


async def main() -> None:
    config = ScraperConfig(
        output_dir="output",
        output_format="json",
        timeout=15.0,
    )

    pipeline = Pipeline()
    pipeline.add_step(strip_whitespace)
    pipeline.add_step(deduplicate_links)

    engine = ScraperEngine(config, pipeline)
    pages = await engine.run(["https://httpbin.org/html"])
    paths = engine.export(pages)

    for page in pages:
        print(f"Title: {page.title}")
        print(f"Links: {len(page.links)}")
        print(f"Images: {len(page.images)}")
        print(f"Text preview: {page.text[:200]}...")
        print()

    print(f"Exported to: {paths}")


if __name__ == "__main__":
    asyncio.run(main())
