"""Graduate Studies course timetable scraper."""

import json
from pathlib import Path

from helpers.html_io import read_scraping_html
from helpers.parser import parse_course_timetable_html
from helpers.term_paths import fall_winter_paths


def main():
    scraping_dir = Path(__file__).resolve().parents[2]
    html_path, data_path = fall_winter_paths(scraping_dir, "graduate_studies")

    try:
        html_content = read_scraping_html(html_path)
    except Exception as error:
        print(f"Error reading HTML: {error}")
        return

    try:
        result = parse_course_timetable_html(html_content, extract_metadata=False)
        data_path.parent.mkdir(parents=True, exist_ok=True)
        data_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Saved: {data_path}")
        print(f"Courses: {len(result.get('courses', []))}")
        for index, course in enumerate(result.get('courses', []), 1):
            section_letters = sorted({section.get('section', '') for section in course.get('sections', []) if section.get('section')})
            section_display = ",".join(section_letters)
            print(f"{index}. {course.get('courseId','')} - {course.get('courseTitle','')} (Section: {section_display})")
    except Exception as error:
        print(f"Error parsing HTML: {error}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()