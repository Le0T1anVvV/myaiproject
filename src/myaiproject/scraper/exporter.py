"""Exports scraped data to JSON or CSV format."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from myaiproject.scraper.parser import ParsedPage


class Exporter:
    """Writes ParsedPage results to disk."""

    def __init__(self, output_dir: str) -> None:
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def export(
        self, pages: list[ParsedPage], fmt: str = "json"
    ) -> list[Path]:
        """Export pages in the given format. Returns list of written file paths."""
        if fmt == "csv":
            return [self._export_csv(pages)]
        return [self._export_json(pages)]

    def _export_json(self, pages: list[ParsedPage]) -> Path:
        path = self._output_dir / "output.json"
        data = [_page_to_dict(p) for p in pages]
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return path

    def _export_csv(self, pages: list[ParsedPage]) -> Path:
        path = self._output_dir / "output.csv"
        with path.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "url", "title", "summary", "text",
                    "links", "images", "metadata",
                ],
            )
            writer.writeheader()
            for page in pages:
                writer.writerow({
                    "url": page.url,
                    "title": page.title,
                    "summary": page.summary,
                    "text": page.text[:2000],
                    "links": "|".join(page.links[:50]),
                    "images": "|".join(page.images[:20]),
                    "metadata": json.dumps(page.metadata, ensure_ascii=False),
                })
        return path


def _page_to_dict(page: ParsedPage) -> dict[str, object]:
    return {
        "url": page.url,
        "title": page.title,
        "summary": page.summary,
        "text": page.text,
        "links": page.links,
        "images": page.images,
        "metadata": page.metadata,
    }
