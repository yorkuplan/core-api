#!/usr/bin/env python3
"""Match course descriptions from JSON files to courses in seed.sql.

This script:
1. Reads all JSON files from scraping/data/courses
2. Extracts course descriptions (dept + code -> desc)
3. Parses seed.sql to get all unique course codes
4. Matches courses and creates course_descriptions.json
5. Tracks unmatched courses in unmatched_courses.txt
"""

import json
import re
from pathlib import Path
from typing import Dict, Set, Tuple


def read_course_descriptions_from_json_files(courses_dir: Path) -> Dict[str, str]:
    """Read all JSON files and extract course descriptions.
    
    Returns:
        Dictionary mapping course_code (e.g., "PSYC1010") to description
    """
    descriptions = {}
    
    json_files = sorted(courses_dir.glob("*.json"))
    print(f"Found {len(json_files)} JSON files")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            courses = data.get('courses', [])
            for course in courses:
                dept = course.get('dept', '').upper()
                code = course.get('code', '')
                desc = course.get('desc', '').strip()
                
                if dept and code and desc:
                    course_code = f"{dept}{code}"
                    # If duplicate, keep the first one (or we could merge)
                    if course_code not in descriptions:
                        descriptions[course_code] = desc
                    elif descriptions[course_code] != desc:
                        # Log if there's a mismatch (same course code, different description)
                        print(f"  Warning: Duplicate course code {course_code} with different descriptions")
        
        except Exception as e:
            print(f"  Error reading {json_file.name}: {e}")
            continue
    
    print(f"Extracted {len(descriptions)} course descriptions")
    return descriptions


def extract_course_codes_from_seed(seed_file: Path) -> Set[str]:
    """Extract all unique course codes from seed.sql.
    
    Returns:
        Set of course codes (e.g., {"PSYC1010", "ADMS1000", ...})
    """
    course_codes = set()
    
    # Pattern to match INSERT INTO courses lines
    # Format: ('id', 'name', 'code', credits, description, faculty, term)
    pattern = r"INSERT INTO courses.*?VALUES\s*"
    
    with open(seed_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all INSERT statements
    insert_pattern = r"\('([^']+)',\s*'([^']+)',\s*'([^']+)',\s*([^,]+),\s*([^,]+),\s*'([^']+)',\s*'([^']+)'\)"
    
    matches = re.findall(insert_pattern, content)
    
    for match in matches:
        course_code = match[2]  # Third field is the code
        if course_code:
            course_codes.add(course_code)
    
    print(f"Found {len(course_codes)} unique course codes in seed.sql")
    return course_codes


def create_course_descriptions_json(
    descriptions: Dict[str, str],
    seed_course_codes: Set[str],
    output_file: Path,
    unmatched_file: Path
) -> None:
    """Create course_descriptions.json and track unmatched courses.
    
    Args:
        descriptions: Dictionary of course_code -> description from JSON files
        seed_course_codes: Set of course codes from seed.sql
        output_file: Path to write course_descriptions.json
        unmatched_file: Path to write unmatched_courses.txt
    """
    matched_descriptions = {}
    unmatched_courses = []
    
    for course_code in sorted(seed_course_codes):
        if course_code in descriptions:
            matched_descriptions[course_code] = descriptions[course_code]
        else:
            unmatched_courses.append(course_code)
    
    # Write course_descriptions.json
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(matched_descriptions, f, indent=2, ensure_ascii=False)
    
    print(f"\nMatched: {len(matched_descriptions)} courses")
    print(f"Unmatched: {len(unmatched_courses)} courses")
    print(f"Saved course_descriptions.json to: {output_file}")
    
    # Write unmatched courses to text file
    unmatched_file.parent.mkdir(parents=True, exist_ok=True)
    with open(unmatched_file, 'w', encoding='utf-8') as f:
        f.write("Courses from seed.sql that were not found in the JSON files:\n")
        f.write("=" * 70 + "\n\n")
        for course_code in sorted(unmatched_courses):
            f.write(f"{course_code}\n")
    
    print(f"Saved unmatched courses to: {unmatched_file}")
    
    # Also track courses in JSON files that aren't in seed.sql
    json_only_courses = []
    for course_code in descriptions:
        if course_code not in seed_course_codes:
            json_only_courses.append(course_code)
    
    if json_only_courses:
        json_only_file = unmatched_file.parent / "courses_in_json_not_in_seed.txt"
        with open(json_only_file, 'w', encoding='utf-8') as f:
            f.write("Courses in JSON files that are not in seed.sql:\n")
            f.write("=" * 70 + "\n\n")
            for course_code in sorted(json_only_courses):
                f.write(f"{course_code}\n")
        print(f"Found {len(json_only_courses)} courses in JSON files not in seed.sql")
        print(f"Saved to: {json_only_file}")


def main():
    """Main entry point."""
    # Get paths
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    courses_dir = project_root / "scraping" / "data" / "courses"
    seed_file = project_root / "db" / "seed.sql"
    output_file = project_root / "scraping" / "data" / "course_descriptions.json"
    unmatched_file = project_root / "scraping" / "data" / "unmatched_courses.txt"
    
    print("=" * 70)
    print("COURSE DESCRIPTION MATCHER")
    print("=" * 70)
    print(f"Courses directory: {courses_dir}")
    print(f"Seed file: {seed_file}")
    print(f"Output file: {output_file}")
    print(f"Unmatched file: {unmatched_file}")
    print()
    
    # Step 1: Read course descriptions from JSON files
    print("Step 1: Reading course descriptions from JSON files...")
    descriptions = read_course_descriptions_from_json_files(courses_dir)
    print()
    
    # Step 2: Extract course codes from seed.sql
    print("Step 2: Extracting course codes from seed.sql...")
    seed_course_codes = extract_course_codes_from_seed(seed_file)
    print()
    
    # Step 3: Match and create output files
    print("Step 3: Matching courses and creating output files...")
    create_course_descriptions_json(descriptions, seed_course_codes, output_file, unmatched_file)
    print()
    
    print("=" * 70)
    print("DONE")
    print("=" * 70)


if __name__ == "__main__":
    main()
