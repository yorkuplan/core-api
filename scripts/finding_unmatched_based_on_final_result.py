#!/usr/bin/env python3
"""Find courses with missing descriptions in final scraped JSON files.

This script:
1. Reads all final JSON files from scraping/data (not scraping/data/courses)
2. Checks which courses have empty descriptions ("")
3. Produces a list of courses missing descriptions in the final results
"""

import json
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict


def find_courses_with_missing_descriptions(data_dir: Path) -> Dict[str, List[Dict]]:
    """Find all courses with empty descriptions in final JSON files.
    
    Args:
        data_dir: Path to scraping/data directory
    
    Returns:
        Dictionary mapping filename to list of courses with missing descriptions
    """
    missing_by_file = {}
    
    # Find all JSON files in data directory (excluding courses subdirectory)
    json_files = [f for f in data_dir.glob("*.json") 
                  if f.name != "course_descriptions.json" 
                  and f.name != "course_descriptions_old.json"]
    
    print(f"Found {len(json_files)} final JSON files to check")
    print()
    
    total_courses = 0
    total_with_desc = 0
    total_missing_desc = 0
    
    for json_file in sorted(json_files):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            courses = data.get('courses', [])
            if not courses:
                continue
            
            missing_courses = []
            file_total = len(courses)
            file_with_desc = 0
            file_missing_desc = 0
            
            for course in courses:
                dept = course.get('department', '').strip()
                code = course.get('courseId', '').strip()
                desc = course.get('description', '').strip()
                
                if dept and code:
                    course_code = f"{dept}{code}"
                    
                    if desc:
                        file_with_desc += 1
                    else:
                        file_missing_desc += 1
                        missing_courses.append({
                            'course_code': course_code,
                            'department': dept,
                            'courseId': code,
                            'title': course.get('courseTitle', ''),
                            'faculty': course.get('faculty', ''),
                            'term': course.get('term', '')
                        })
            
            if missing_courses:
                missing_by_file[json_file.name] = missing_courses
            
            total_courses += file_total
            total_with_desc += file_with_desc
            total_missing_desc += file_missing_desc
            
            print(f"{json_file.name}:")
            print(f"  Total courses: {file_total}")
            print(f"  With descriptions: {file_with_desc} ({file_with_desc/file_total*100:.1f}%)")
            print(f"  Missing descriptions: {file_missing_desc} ({file_missing_desc/file_total*100:.1f}%)")
            print()
        
        except Exception as e:
            print(f"  Error reading {json_file.name}: {e}")
            continue
    
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total courses across all files: {total_courses:,}")
    print(f"With descriptions: {total_with_desc:,} ({total_with_desc/total_courses*100:.1f}%)")
    print(f"Missing descriptions: {total_missing_desc:,} ({total_missing_desc/total_courses*100:.1f}%)")
    print()
    
    return missing_by_file


def create_missing_descriptions_report(
    missing_by_file: Dict[str, List[Dict]],
    output_file: Path
) -> None:
    """Create a report of courses with missing descriptions.
    
    Args:
        missing_by_file: Dictionary mapping filename to list of courses with missing descriptions
        output_file: Path to write the report
    """
    # Collect all unique course codes
    all_missing_courses = {}
    courses_by_dept = defaultdict(list)
    
    for filename, courses in missing_by_file.items():
        for course in courses:
            course_code = course['course_code']
            # Keep track of which files contain this course
            if course_code not in all_missing_courses:
                all_missing_courses[course_code] = {
                    'course_code': course_code,
                    'department': course['department'],
                    'courseId': course['courseId'],
                    'title': course['title'],
                    'files': []
                }
            all_missing_courses[course_code]['files'].append(filename)
            courses_by_dept[course['department']].append(course_code)
    
    # Write detailed report
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("Courses Missing Descriptions in Final Scraped Results\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Total unique courses missing descriptions: {len(all_missing_courses)}\n")
        f.write(f"Generated from final JSON files in scraping/data/\n\n")
        
        # Summary by department
        f.write("Missing descriptions by department:\n")
        f.write("-" * 70 + "\n")
        sorted_depts = sorted(courses_by_dept.items(), key=lambda x: len(set(x[1])), reverse=True)
        for dept, codes in sorted_depts:
            unique_codes = len(set(codes))
            f.write(f"  {dept}: {unique_codes} unique courses\n")
        
        f.write("\n" + "=" * 70 + "\n\n")
        
        # Detailed list by file
        f.write("Missing descriptions by file:\n")
        f.write("=" * 70 + "\n\n")
        for filename in sorted(missing_by_file.keys()):
            courses = missing_by_file[filename]
            f.write(f"{filename} ({len(courses)} courses):\n")
            f.write("-" * 70 + "\n")
            for course in sorted(courses, key=lambda x: x['course_code']):
                f.write(f"  {course['course_code']} - {course['title']}\n")
            f.write("\n")
        
        f.write("\n" + "=" * 70 + "\n\n")
        
        # Unique course codes list
        f.write("All unique courses missing descriptions (sorted by course code):\n")
        f.write("=" * 70 + "\n\n")
        for course_code in sorted(all_missing_courses.keys()):
            course_info = all_missing_courses[course_code]
            f.write(f"{course_code} - {course_info['title']}\n")
            f.write(f"  Found in: {', '.join(sorted(course_info['files']))}\n\n")
    
    print(f"Saved detailed report to: {output_file}")
    
    # Also create a simple list file
    simple_list_file = output_file.parent / "missing_descriptions_simple_list.txt"
    with open(simple_list_file, 'w', encoding='utf-8') as f:
        f.write("Unique course codes missing descriptions in final results:\n")
        f.write("=" * 70 + "\n\n")
        for course_code in sorted(all_missing_courses.keys()):
            f.write(f"{course_code}\n")
    
    print(f"Saved simple list to: {simple_list_file}")
    print(f"\nTotal unique courses missing descriptions: {len(all_missing_courses)}")


def main():
    """Main entry point."""
    # Get paths
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    data_dir = project_root / "scraping" / "data"
    output_file = project_root / "scraping" / "data" / "missing_descriptions_in_final_results.txt"
    
    print("=" * 70)
    print("FINDING MISSING DESCRIPTIONS IN FINAL RESULTS")
    print("=" * 70)
    print(f"Data directory: {data_dir}")
    print(f"Output file: {output_file}")
    print()
    
    # Find courses with missing descriptions
    missing_by_file = find_courses_with_missing_descriptions(data_dir)
    
    if not missing_by_file:
        print("No courses with missing descriptions found!")
        return
    
    # Create report
    print("\nCreating report...")
    create_missing_descriptions_report(missing_by_file, output_file)
    
    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)


if __name__ == "__main__":
    main()
