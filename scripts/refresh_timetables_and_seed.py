#!/usr/bin/env python3
"""
Download SIS timetable HTML, run all scrapers, regenerate db/seed.sql.

Typical use (from repo root, with network):

  python3 scripts/refresh_timetables_and_seed.py

If SIS returns Passport York instead of timetables, pass a browser Cookie header:

  python3 scripts/refresh_timetables_and_seed.py --cookie 'name=value; ...'

Options mirror scripts/fetch_page_sources.py where relevant (--only, --delay, etc.).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def run_step(cmd: list[str], *, cwd: Path) -> None:
    print("\n+ " + " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> int:
    root = repo_root()
    py = sys.executable
    fetch = str(root / "scripts" / "fetch_page_sources.py")
    scrape = str(root / "scraping" / "scrapers" / "scrape.py")
    gen = str(root / "scripts" / "generate_seed.py")

    p = argparse.ArgumentParser(description="Fetch HTML → scrape JSON → db/seed.sql")
    p.add_argument(
        "--fw-term",
        default="fall-winter-2026-2027",
        metavar="FOLDER",
        help="page_source / data subfolder for fall-winter (default: fall-winter-2026-2027)",
    )
    p.add_argument(
        "--summer-term",
        default="summer-2026",
        metavar="FOLDER",
        help="page_source subfolder for summer static HTML (default: summer-2026)",
    )
    p.add_argument("--skip-fetch", action="store_true", help="Do not download HTML")
    p.add_argument(
        "--skip-summer-fetch",
        action="store_true",
        help="Only fetch fall/winter HTML (leave summer page_source as-is)",
    )
    p.add_argument("--only", default="", help="Comma-separated stems for fetch_page_sources --only")
    p.add_argument("--fetch-delay", type=float, default=10.0, help="Seconds between fetch requests")
    p.add_argument("--timeout", type=int, default=60, help="HTTP timeout for fetch")
    p.add_argument("--referer", default="https://apps1.sis.yorku.ca/", help="Referer for fetch")
    p.add_argument(
        "--cookie",
        default="",
        help="Cookie header for authenticated SIS fetch (see fetch_page_sources.py)",
    )
    p.add_argument("--dry-run-fetch", action="store_true", help="Print fetch URLs only")
    args = p.parse_args()

    scrape_cwd = root / "scraping" / "scrapers"

    if not args.skip_fetch:
        def fetch_cmd(term: str) -> list[str]:
            cmd = [
                py,
                fetch,
                "--term",
                term,
                "--delay",
                str(args.fetch_delay),
                "--timeout",
                str(args.timeout),
                "--referer",
                args.referer,
            ]
            if args.only:
                cmd.extend(["--only", args.only])
            if args.cookie:
                cmd.extend(["--cookie", args.cookie])
            if args.dry_run_fetch:
                cmd.append("--dry-run")
            return cmd

        run_step(fetch_cmd(args.fw_term), cwd=root)
        if not args.skip_summer_fetch:
            run_step(fetch_cmd(args.summer_term), cwd=root)

    run_step(
        [py, scrape, "--fall-winter-term", args.fw_term],
        cwd=scrape_cwd,
    )

    run_step(
        [py, gen, args.fw_term, args.summer_term],
        cwd=root,
    )

    print("\nDone: page_source updated (unless --skip-fetch), JSON scraped, db/seed.sql regenerated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
