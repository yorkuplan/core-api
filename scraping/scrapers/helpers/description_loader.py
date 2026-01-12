"""Helper to load and add course descriptions from course_descriptions.json."""

import json
from pathlib import Path
from typing import Dict, Any, Optional


def load_course_descriptions(scraping_dir: Path) -> Dict[str, str]:
    """Load course descriptions from course_descriptions.json.
    
    Args:
        scraping_dir: Path to scraping directory (parent of data/)
    
    Returns:
        Dictionary mapping course_code (e.g., "PSYC1010") to description
    """
    descriptions_file = scraping_dir / "data" / "course_descriptions.json"
    
    if not descriptions_file.exists():
        print(f"Warning: course_descriptions.json not found at {descriptions_file}")
        return {}
    
    try:
        with open(descriptions_file, 'r', encoding='utf-8') as f:
            descriptions = json.load(f)
        print(f"Loaded {len(descriptions)} course descriptions")
        return descriptions
    except Exception as e:
        print(f"Error loading course_descriptions.json: {e}")
        return {}


def add_descriptions_to_courses(courses: list[Dict[str, Any]], descriptions: Dict[str, str]) -> None:
    """Add description field to each course in the courses list.
    
    Args:
        courses: List of course dictionaries (modified in place)
        descriptions: Dictionary mapping course_code to description
    """
    matched_count = 0
    unmatched_count = 0
    
    for course in courses:
        department = course.get("department", "").strip()
        course_id = course.get("courseId", "").strip()
        
        if department and course_id:
            # Try exact match first
            course_code = f"{department}{course_id}"
            description = descriptions.get(course_code)
            
            # If no exact match and course_id ends with a letter, try without the letter
            if not description and course_id and course_id[-1].isalpha():
                course_code_base = f"{department}{course_id[:-1]}"
                description = descriptions.get(course_code_base)
            
            # If still no match, try to find any course that starts with department + numeric part
            if not description:
                # Extract numeric part of course_id
                numeric_part = ''.join(c for c in course_id if c.isdigit())
                if numeric_part:
                    course_code_base = f"{department}{numeric_part}"
                    # Try to find any matching course (with or without suffix)
                    for key in descriptions:
                        if key.startswith(course_code_base):
                            description = descriptions[key]
                            break
            
            if description:
                course["description"] = description
                matched_count += 1
            else:
                # No description found, set to empty string
                course["description"] = ""
                unmatched_count += 1
        else:
            # Missing department or courseId
            course["description"] = ""
            unmatched_count += 1
    
    if matched_count > 0:
        print(f"Added descriptions to {matched_count} courses")
    if unmatched_count > 0:
        print(f"Warning: {unmatched_count} courses did not have matching descriptions")
