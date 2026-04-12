"""Read saved timetable HTML; supports UTF-8 and UTF-16 (some browsers/tools save with BOM)."""

from pathlib import Path


def read_scraping_html(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16")
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig")
    return raw.decode("utf-8", errors="replace")
