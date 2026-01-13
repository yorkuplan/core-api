"""
Clean and transform courses_data.json to extract course codes and descriptions only
"""

import json
import re

def extract_course_code(course_id):
    """
    Extract course code from course_id string
    Format: "AP/ANTH 1120 6.00   Making Sense of..."
    Extract: "ANTH 1120" and convert to "ANTH1120"
    """
    # Pattern: Subject code (2-4 letters), space, 4 digits, then optional letters/numbers
    match = re.search(r'([A-Z]{2,4})\s+(\d{4}[A-Z]?)', course_id)
    if match:
        subject = match.group(1)
        number = match.group(2)
        return f"{subject}{number}"
    return None

def clean_courses(input_file='courses_data.json', output_file='course_descriptions.json'):
    """Transform courses data to clean format"""
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Processing {len(data)} courses...")
        
        cleaned_data = []
        skipped_count = 0
        
        for entry in data:
            course_id = entry.get('course_id', '').strip()
            description = entry.get('description', '').strip()
            
            # Extract course code
            course_code = extract_course_code(course_id)
            
            if not course_code:
                print(f"⚠️  Could not extract code from: {course_id}")
                skipped_count += 1
                continue
            
            # Use N/A if description is missing
            if not description or description.lower() == 'description not found':
                description = "N/A"
            
            cleaned_data.append({
                "course_code": course_code,
                "description": description
            })
        
        # Save cleaned data
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*60}")
        print(f"✅ Original entries: {len(data)}")
        print(f"✅ Cleaned entries: {len(cleaned_data)}")
        print(f"✅ Output file: {output_file}")
        print(f"{'='*60}\n")
        
        return cleaned_data
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    print("Cleaning courses data...\n")
    cleaned = clean_courses()
    
    if cleaned:
        print("Sample entries from output:")
        for entry in cleaned[:3]:
            print(f"\nCourse Code: {entry['course_code']}")
            print(f"Description: {entry['description'][:100]}...")
