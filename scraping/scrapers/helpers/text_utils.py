"""Text processing utilities for scrapers."""

import html
import re


def norm_text(text: str) -> str:
    """Normalize text by unescaping HTML entities, collapsing whitespace, and trimming."""
    if text is None:
        return ""
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def html_to_text(html_fragment: str, br_separator: str = "|") -> str:
    """Convert an HTML fragment to plain text.
    - Replaces <br> with the given separator
    - Strips all HTML tags
    - Unescapes HTML entities
    - Collapses whitespace and trims
    """
    if not html_fragment:
        return ""
    text = html.unescape(html_fragment)
    text = re.sub(r"<br\s*/?>", br_separator, text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

