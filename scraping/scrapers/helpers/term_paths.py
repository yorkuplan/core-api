"""Resolve page_source / data folders for timetable scrapers."""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_FALL_WINTER_TERM = "fall-winter-2025-2026"


def fall_winter_term() -> str:
    """Subfolder under scraping/page_source and scraping/data (env FALL_WINTER_TERM)."""
    t = os.environ.get("FALL_WINTER_TERM", DEFAULT_FALL_WINTER_TERM).strip()
    return t or DEFAULT_FALL_WINTER_TERM


def fall_winter_paths(scraping_dir: Path, stem: str) -> tuple[Path, Path]:
    """HTML input and JSON output paths for one fall/winter faculty scraper."""
    term = fall_winter_term()
    html_path = scraping_dir / "page_source" / term / f"{stem}.html"
    data_path = scraping_dir / "data" / term / f"{stem}.json"
    return html_path, data_path
