#!/usr/bin/env python3
"""
Compare course counts: HTML page_source vs scraped JSON.

Uses the same rules as the scraper (first <table>, rows where is_header_row).
Also re-runs parse_course_timetable_html and compares to JSON on disk.

Usage:
  python3 scripts/verify_page_source_vs_json.py --term fall-winter-2026-2027
  python3 scripts/verify_page_source_vs_json.py --term summer-2026
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from bs4 import BeautifulSoup


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def setup_scraper_path() -> None:
    root = repo_root()
    scrapers = root / "scraping" / "scrapers"
    sys.path.insert(0, str(scrapers / "fall-winter-2025-2026"))
    sys.path.insert(1, str(scrapers))


def count_header_rows(html: str, is_header_row) -> tuple[int, str]:
    """Return (count, note). count -1 if no table."""
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return -1, "no <table>"
    n = sum(1 for tr in table.find_all("tr") if is_header_row(tr))
    return n, ""


def count_parsed_courses(html: str, parse_course_timetable_html) -> int:
    return len(parse_course_timetable_html(html, extract_metadata=False).get("courses", []))


def main() -> int:
    root = repo_root()
    p = argparse.ArgumentParser(description="Verify JSON course counts vs page_source HTML")
    p.add_argument(
        "--term",
        required=True,
        help="Subfolder under scraping/page_source and scraping/data (e.g. fall-winter-2026-2027)",
    )
    args = p.parse_args()

    page_dir = root / "scraping" / "page_source" / args.term
    data_dir = root / "scraping" / "data" / args.term
    if not page_dir.is_dir():
        print(f"Missing page_source dir: {page_dir}", file=sys.stderr)
        return 1
    if not data_dir.is_dir():
        print(f"Missing data dir: {data_dir}", file=sys.stderr)
        return 1

    setup_scraper_path()
    from helpers.course_parsing import is_header_row
    from helpers.html_io import read_scraping_html
    from helpers.parser import parse_course_timetable_html

    html_files = sorted(page_dir.glob("*.html"))
    if not html_files:
        print(f"No HTML files in {page_dir}", file=sys.stderr)
        return 1

    mismatches = 0
    print(f"{'stem':<28} {'headers':>8} {'parsed':>8} {'json':>8}  ok")
    print("-" * 64)

    for html_path in html_files:
        stem = html_path.stem
        json_path = data_dir / f"{stem}.json"
        try:
            html = read_scraping_html(html_path)
        except OSError as e:
            print(f"{stem:<28} {'ERROR':>8} {e}", file=sys.stderr)
            mismatches += 1
            continue

        hdrs, _note = count_header_rows(html, is_header_row)

        try:
            parsed_n = count_parsed_courses(html, parse_course_timetable_html)
        except Exception as e:
            print(f"{stem:<28} parse error: {e}", file=sys.stderr)
            mismatches += 1
            continue

        if not json_path.is_file():
            print(f"{stem:<28} {hdrs_display:>8} {parsed_n:>8} {'(missing json)':>8}")
            mismatches += 1
            continue

        with json_path.open(encoding="utf-8") as f:
            json_n = len(json.load(f).get("courses", []))

        ok = hdrs == parsed_n == json_n and hdrs >= 0
        flag = "yes" if ok else "NO"
        if not ok:
            mismatches += 1
        print(f"{stem:<28} {hdrs:>8} {parsed_n:>8} {json_n:>8}  {flag}")

    print("-" * 64)
    if mismatches:
        print(f"Mismatch or error count: {mismatches}")
        return 1
    print("All counts match (header rows == full parse == JSON).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
