"""Tests for helpers.html_io."""

import tempfile
import unittest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from helpers.html_io import read_scraping_html


class TestReadScrapingHtml(unittest.TestCase):
    def test_utf8(self) -> None:
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".html") as f:
            f.write("<table></table>".encode("utf-8"))
            p = Path(f.name)
        try:
            self.assertIn("<table>", read_scraping_html(p))
        finally:
            p.unlink(missing_ok=True)

    def test_utf16_bom(self) -> None:
        text = "<HTML><table></table></HTML>"
        raw = text.encode("utf-16")
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".html") as f:
            f.write(raw)
            p = Path(f.name)
        try:
            out = read_scraping_html(p)
            self.assertIn("table", out.lower())
        finally:
            p.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
