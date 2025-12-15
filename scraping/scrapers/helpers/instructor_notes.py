"""Instructor and notes parsing utilities."""

import re
from typing import List

from .text_utils import norm_text, html_to_text


def parse_instructors(instructor_html: str) -> List[str]:
    """Parse instructor HTML into a list of instructor names, handling separators and HTML artifacts."""
    if not instructor_html:
        return []
    text = html_to_text(instructor_html, br_separator="|")
    parts = re.split(r"[|,;&]", text)
    instructors_list: List[str] = []
    for part in parts:
        name = norm_text(part)
        if name and name.lower() not in {"nbsp", "amp", "lt", "gt"}:
            instructors_list.append(name)
    return instructors_list


def parse_notes(notes_html: str) -> str:
    """Parse notes HTML into a single normalized string, preserving line breaks via ' | '."""
    if not notes_html:
        return ""
    text = html_to_text(notes_html, br_separator=" | ")
    return text.strip(" |")

