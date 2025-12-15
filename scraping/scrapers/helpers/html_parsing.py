"""HTML parsing utilities."""

from bs4 import Tag
from typing import Optional

from .text_utils import norm_text


def cell_text(element: Optional[Tag]) -> str:
    """Extract text from a BeautifulSoup element with normalized spacing and trimming."""
    if element is None:
        return ""
    text = element.get_text(" ", strip=True)
    text = text.replace("\xa0", " ")
    return norm_text(text)

