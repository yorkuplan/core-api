"""
Main parser orchestration utilities.

This is where the parsing is initiated.
"""

from bs4 import BeautifulSoup, Tag
from typing import Dict, Any, List

from .html_parsing import cell_text
from .course_parsing import (
    is_header_row,
    parse_course_header,
    parse_section_row,
)


def parse_course_timetable_html(html_content: str, extract_metadata: bool = False, allow_alphanumeric_course_id: bool = True) -> Dict[str, Any]:
    """Parse HTML timetable into structured course data.
    
    Args:
        html_content: HTML content string
        extract_metadata: If True, extracts title and lastUpdated from page (default: False)
        allow_alphanumeric_course_id: If True, allows course IDs like "4800Q" (default: True)
    
    Returns:
        Dictionary with 'courses' list, and optionally 'metadata' dict
    """
    soup = BeautifulSoup(html_content, "html.parser")

    metadata = None
    if extract_metadata:
        title = cell_text(soup.select_one("p.heading"))
        last_updated = ""
        for body_paragraph in soup.select("p.bodytext"):
            strong = body_paragraph.find("strong")
            if strong:
                last_updated = cell_text(strong)
                break
        metadata = {"title": title, "lastUpdated": last_updated, "source": "York University"}

    table = soup.find("table")
    if not table:
        if metadata:
            return {"metadata": metadata, "courses": []}
        return {"courses": []}

    # Orchestrate parsing with module-level helpers
    courses: List[Dict[str, Any]] = []
    header_rows = [table_row for table_row in table.find_all("tr") if is_header_row(table_row)]
    for header_row in header_rows:
        course = parse_course_header(header_row)
        for element in header_row.next_elements:
            if not isinstance(element, Tag):
                continue
            if element is header_row:
                continue
            if element.name != "tr":
                continue
            if is_header_row(element):
                break
            row_cells = element.find_all("td", recursive=False)
            if not row_cells:
                continue
            section_detail = parse_section_row(row_cells, course, allow_alphanumeric_course_id)
            if section_detail is not None:
                course["sections"].append(section_detail)
        courses.append(course)

    result = {"courses": courses}
    if metadata:
        result["metadata"] = metadata
    return result

