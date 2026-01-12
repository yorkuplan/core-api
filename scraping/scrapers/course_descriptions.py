"""Course description scraper using browser automation.

This scraper navigates through York University's course search system to extract
course descriptions by:
1. Starting at the course search page
2. Iterating through all subjects
3. For each subject, iterating through all courses
4. Extracting course descriptions from course detail pages
"""

import json
import sys
import time
import random
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeoutError

from helpers.browser_utils import (
    init_browser,
    create_context,
    wait_for_page_load,
    safe_click,
    safe_select_option,
    get_text_content,
    get_all_options,
    navigate_with_retry,
)


# Base URL for the course search page
# The URL with the long path might be session-specific, so we'll start from the base
BASE_URL = "https://w2prod.sis.yorku.ca/Apps/WebObjects/cdm.woa"
SEARCH_URL = "https://w2prod.sis.yorku.ca/Apps/WebObjects/cdm.woa/10/wo/fJcxw3tUjA3Oixp3wo8dpg/0.3.10.21"

# CSS selectors (these may need adjustment based on actual page structure)
SUBJECT_SELECTOR = "select[name*='subject'], select[id*='subject'], select[name*='Subject'], select[id*='Subject']"
SEARCH_BUTTON_SELECTOR = "input[type='submit'][value*='Search'], button:has-text('Search'), input[value*='Search Courses']"
COURSE_SCHEDULE_LINK_SELECTOR = "a:has-text('Fall/Winter 2025-2026 Course Schedule')"
COURSE_TITLE_SELECTOR = "h1, h2, .course-title, p.heading"
COURSE_DESCRIPTION_SELECTOR = "p.bodytext, .course-description, .description"


def find_subject_dropdown(page: Page) -> Optional[str]:
    """Find the subject dropdown selector on the page.
    
    Args:
        page: Page instance
    
    Returns:
        CSS selector for the subject dropdown, or None if not found
    """
    # Wait a bit for page to fully load
    time.sleep(2)
    
    # Try multiple possible selectors (case-insensitive)
    selectors = [
        "select[name*='subject' i]",
        "select[id*='subject' i]",
        "select[name*='Subject']",
        "select[id*='Subject']",
        "select[name*='SUBJECT']",
        "select[id*='SUBJECT']",
        "select",  # Try all selects as fallback
    ]
    
    for selector in selectors:
        try:
            # Wait for selector to appear
            page.wait_for_selector(selector, timeout=5000, state="attached")
            elements = page.query_selector_all(selector)
            for element in elements:
                # Check if this looks like a subject dropdown
                options = element.query_selector_all("option")
                if len(options) > 10:  # Subject dropdown should have many options
                    # Check if options look like subject codes
                    subject_like_count = 0
                    for option in options[:10]:
                        value = option.get_attribute("value") or ""
                        text = option.inner_text().strip()
                        # Subject codes are typically 2-10 alphanumeric chars
                        if value and 2 <= len(value) <= 10 and (value.isalnum() or "/" in value):
                            subject_like_count += 1
                        elif text and 2 <= len(text.split()[0]) <= 10:
                            subject_like_count += 1
                    
                    # If at least 3 options look like subjects, this is probably it
                    if subject_like_count >= 3:
                        name = element.get_attribute("name") or ""
                        id_attr = element.get_attribute("id") or ""
                        if name:
                            return f"select[name='{name}']"
                        elif id_attr:
                            return f"select[id='{id_attr}']"
                        else:
                            # Use index-based selector as last resort
                            all_selects = page.query_selector_all("select")
                            idx = all_selects.index(element)
                            return f"select:nth-of-type({idx + 1})"
        except Exception:
            continue
    
    # Final fallback: try to find by label text
    try:
        # Look for label containing "Subject" and find associated select
        labels = page.query_selector_all("label")
        for label in labels:
            label_text = label.inner_text().strip().lower()
            if "subject" in label_text:
                # Try to find associated select via 'for' attribute
                for_attr = label.get_attribute("for")
                if for_attr:
                    select = page.query_selector(f"select[id='{for_attr}']")
                    if select:
                        return f"select[id='{for_attr}']"
                
                # Or find select that follows the label using evaluate
                next_sibling_info = label.evaluate("""
                    el => {
                        const next = el.nextElementSibling;
                        if (next && next.tagName === 'SELECT') {
                            return {
                                name: next.name || '',
                                id: next.id || ''
                            };
                        }
                        return null;
                    }
                """)
                if next_sibling_info:
                    if next_sibling_info.get("id"):
                        return f"select[id='{next_sibling_info['id']}']"
                    elif next_sibling_info.get("name"):
                        return f"select[name='{next_sibling_info['name']}']"
    except Exception:
        pass
    
    # Debug: print all selects found
    try:
        all_selects = page.query_selector_all("select")
        print(f"Debug: Found {len(all_selects)} select elements on page")
        for i, sel in enumerate(all_selects[:5]):  # Show first 5
            name = sel.get_attribute("name") or "no-name"
            id_attr = sel.get_attribute("id") or "no-id"
            options_count = len(sel.query_selector_all("option"))
            print(f"  Select {i+1}: name='{name}', id='{id_attr}', options={options_count}")
    except Exception as e:
        print(f"Debug error: {e}")
    
    return None


def find_search_button(page: Page) -> Optional[str]:
    """Find the search button selector on the page.
    
    Args:
        page: Page instance
    
    Returns:
        CSS selector for the search button, or None if not found
    """
    selectors = [
        "input[type='submit'][value*='Search']",
        "input[type='submit'][value*='Search Courses']",
        "button:has-text('Search')",
        "button:has-text('Search Courses')",
        "input[value*='Search']",
    ]
    
    for selector in selectors:
        try:
            element = page.query_selector(selector)
            if element:
                return selector
        except Exception:
            continue
    
    # Fallback: find submit button or button with "Search" text
    try:
        buttons = page.query_selector_all("input[type='submit'], button")
        for button in buttons:
            text = button.inner_text() if button.tag_name() == "button" else button.get_attribute("value") or ""
            if "search" in text.lower():
                if button.tag_name() == "button":
                    return "button"
                else:
                    name = button.get_attribute("name") or ""
                    return f"input[name='{name}'][type='submit']"
    except Exception:
        pass
    
    return None


def extract_course_info_from_results(page: Page) -> List[Dict[str, Any]]:
    """Extract course information from the results page.
    
    Args:
        page: Page instance
    
    Returns:
        List of dictionaries with course_id, course_title, and link_url
    """
    courses = []
    
    try:
        # Wait for the results table to load
        page.wait_for_selector("table", timeout=10000)
        
        # Find all course schedule links
        links = page.query_selector_all(COURSE_SCHEDULE_LINK_SELECTOR)
        
        for link in links:
            try:
                # Get the link URL
                link_url = link.get_attribute("href") or ""
                if not link_url.startswith("http"):
                    # Handle relative URLs
                    base_url = page.url.split("/wo/")[0] if "/wo/" in page.url else page.url
                    link_url = f"{base_url}{link_url}" if link_url.startswith("/") else f"{base_url}/{link_url}"
                
                # Try to find the course ID and title from the table row using evaluate
                row_data = link.evaluate("""
                    el => {
                        const row = el.closest('tr');
                        if (!row) return null;
                        const cells = row.querySelectorAll('td');
                        return {
                            course_id: cells[0] ? cells[0].innerText.trim() : '',
                            course_title: cells[1] ? cells[1].innerText.trim() : ''
                        };
                    }
                """)
                
                course_id = row_data.get("course_id", "") if row_data else ""
                course_title = row_data.get("course_title", "") if row_data else ""
                
                if course_id or link_url:
                    courses.append({
                        "course_id": course_id,
                        "course_title": course_title,
                        "link_url": link_url,
                        "link_text": link.inner_text().strip()
                    })
            except Exception as e:
                print(f"Error extracting course info: {e}")
                continue
    except PlaywrightTimeoutError:
        print("Timeout waiting for results table")
    except Exception as e:
        print(f"Error finding course links: {e}")
    
    return courses


def extract_course_description(page: Page) -> str:
    """Extract the course description from the course detail page.
    
    Args:
        page: Page instance
    
    Returns:
        Course description text, or empty string if not found
    """
    # Wait for page to load
    wait_for_page_load(page, timeout=15000)
    
    # Try multiple selectors to find the description
    selectors = [
        "p.bodytext",
        ".course-description",
        ".description",
        "p:has-text('This')",  # Many descriptions start with "This"
    ]
    
    description = ""
    
    for selector in selectors:
        try:
            elements = page.query_selector_all(selector)
            for element in elements:
                text = element.inner_text().strip()
                # Look for a paragraph that's long enough to be a description
                if len(text) > 100 and "course" in text.lower():
                    description = text
                    break
            if description:
                break
        except Exception:
            continue
    
    # Fallback: find the first long paragraph after the course title
    if not description:
        try:
            # Find course title first and get description using evaluate
            title_selectors = ["h1", "h2", ".course-title", "p.heading"]
            
            for title_selector in title_selectors:
                title_element = page.query_selector(title_selector)
                if title_element:
                    # Find next sibling paragraphs using evaluate
                    desc_text = title_element.evaluate("""
                        el => {
                            let current = el.nextElementSibling;
                            while (current) {
                                if (current.tagName === 'P') {
                                    const text = current.innerText.trim();
                                    if (text.length > 100) {
                                        return text;
                                    }
                                }
                                current = current.nextElementSibling;
                            }
                            return null;
                        }
                    """)
                    if desc_text:
                        description = desc_text
                        break
        except Exception:
            pass
    
    # Final fallback: get all paragraphs and find the longest one that looks like a description
    if not description:
        try:
            paragraphs = page.query_selector_all("p")
            for p in paragraphs:
                text = p.inner_text().strip()
                # Look for paragraphs that are substantial and contain course-related keywords
                if len(text) > 150 and any(keyword in text.lower() for keyword in ["course", "students", "develop", "focus", "study"]):
                    description = text
                    break
        except Exception:
            pass
    
    return description.strip()


def random_delay(min_seconds: float, max_seconds: float) -> None:
    """Sleep for a random duration between min and max seconds.
    
    Args:
        min_seconds: Minimum delay in seconds
        max_seconds: Maximum delay in seconds
    """
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)


def scrape_course_descriptions(
    headless: bool = True,
    max_subjects: Optional[int] = None,
    max_courses_per_subject: Optional[int] = None,
    delay_between_actions: float = 2.0,
    delay_between_courses: float = 3.0,
    delay_between_subjects: float = 5.0,
    break_after_subjects: int = 10,
    break_duration: float = 60.0,
    save_progress_every: int = 5,
    progress_file: Optional[Path] = None
) -> Dict[str, Any]:
    """Main function to scrape course descriptions.
    
    Args:
        headless: Whether to run browser in headless mode (default: True)
        max_subjects: Maximum number of subjects to process (None for all)
        max_courses_per_subject: Maximum number of courses per subject (None for all)
        delay_between_actions: Base delay in seconds between actions (default: 2.0)
        delay_between_courses: Delay in seconds between courses, with randomization (default: 3.0)
        delay_between_subjects: Delay in seconds between subjects, with randomization (default: 5.0)
        break_after_subjects: Take a longer break after this many subjects (default: 10)
        break_duration: Duration of break in seconds (default: 60.0)
        save_progress_every: Save progress after this many subjects (default: 5)
        progress_file: Path to save incremental progress (default: None, uses data_path)
    
    Returns:
        Dictionary with metadata and descriptions
    """
    results = {
        "metadata": {
            "scraped_at": datetime.now().isoformat(),
            "total_subjects": 0,
            "total_courses": 0,
            "successful_courses": 0,
            "failed_courses": 0,
            "last_updated": datetime.now().isoformat(),
            "completed_subjects": []  # Track fully completed subjects
        },
        "descriptions": []
    }
    
    # Load existing progress if available
    completed_subjects = set()
    if progress_file and progress_file.exists():
        try:
            existing_data = json.loads(progress_file.read_text(encoding="utf-8"))
            results["descriptions"] = existing_data.get("descriptions", [])
            completed_subjects = set(existing_data.get("metadata", {}).get("completed_subjects", []))
            print(f"Loaded {len(results['descriptions'])} existing descriptions from progress file")
            if completed_subjects:
                print(f"Found {len(completed_subjects)} completed subjects: {', '.join(sorted(completed_subjects))}")
                print("Will skip these subjects and resume from the next incomplete subject")
        except Exception as e:
            print(f"Could not load progress file: {e}")
    
    with sync_playwright() as playwright:
        browser = init_browser(playwright, headless=headless)
        context = create_context(browser)
        page = context.new_page()
        
        try:
            # First, try navigating to the base URL to initialize a session
            print(f"Initializing session at base URL: {BASE_URL}")
            session_initialized = False
            
            if navigate_with_retry(page, BASE_URL):
                wait_for_page_load(page)
                random_delay(2, 3)
                page_content = page.content()
                # Check if we got a valid page (not an error)
                if "exceeded the maximum time limit" not in page_content:
                    session_initialized = True
                    print("✓ Session initialized successfully")
                else:
                    print("⚠️  Base URL also shows session timeout")
            
            # Try the search URL
            print(f"Navigating to search page: {SEARCH_URL}")
            if not navigate_with_retry(page, SEARCH_URL):
                print("Failed to load search page")
                return results
            
            wait_for_page_load(page)
            random_delay(delay_between_actions * 0.8, delay_between_actions * 1.2)
            
            # Check if we got an error page
            page_content = page.content()
            if "exceeded the maximum time limit" in page_content or "session has been ended" in page_content:
                print("⚠️  Session timeout detected. The URL may be expired or require a fresh session.")
                print("Trying to find navigation link to start a new session...")
                
                # Try to find and click the link to restart
                try:
                    # Look for the "click here" link mentioned in the error message
                    restart_links = page.query_selector_all("a")
                    for link in restart_links:
                        href = link.get_attribute("href") or ""
                        link_text = link.inner_text().strip().lower()
                        # Look for links that mention course description or cdm
                        if ("cdm" in href or "Course Description" in link_text) and "click here" in link_text:
                            print(f"Found restart link: {href}")
                            if not href.startswith("http"):
                                if href.startswith("/"):
                                    href = f"https://w2prod.sis.yorku.ca{href}"
                                else:
                                    href = f"{BASE_URL}/{href}"
                            navigate_with_retry(page, href)
                            wait_for_page_load(page)
                            random_delay(2, 3)
                            break
                except Exception as e:
                    print(f"Could not find restart link: {e}")
                    print("\n💡 SUGGESTION: The URL appears to be session-specific and has expired.")
                    print("   Please manually navigate to the course search page in a browser,")
                    print("   then copy the current URL and update SEARCH_URL in the script.")
                    return results
            
            # Additional wait for dynamic content
            print("Waiting for page content to load...")
            time.sleep(3)
            
            # Check page content again
            page_content = page.content()
            if "exceeded the maximum time limit" in page_content:
                print("❌ Still seeing session timeout. The URL may need to be accessed differently.")
                print("You may need to manually navigate to the course search page in a browser")
                print("and copy a fresh URL, or the page structure may have changed.")
                return results
            
            # Try to wait for any select element to appear
            try:
                page.wait_for_selector("select", timeout=10000, state="attached")
            except Exception:
                print("Warning: No select elements found after waiting")
            
            # Find subject dropdown
            print("Finding subject dropdown...")
            subject_selector = find_subject_dropdown(page)
            if not subject_selector:
                print("Could not find subject dropdown")
                print("Attempting to save page HTML for debugging...")
                try:
                    html_content = page.content()
                    scraping_dir = Path(__file__).resolve().parents[1]
                    debug_path = scraping_dir / "page_source" / "course_search_debug.html"
                    debug_path.parent.mkdir(parents=True, exist_ok=True)
                    debug_path.write_text(html_content, encoding="utf-8")
                    print(f"Page HTML saved to: {debug_path}")
                    print("You can inspect this file to see the actual page structure")
                except Exception as e:
                    print(f"Could not save debug HTML: {e}")
                return results
            
            print(f"Found subject dropdown: {subject_selector}")
            
            # Get all subjects
            subjects = get_all_options(page, subject_selector)
            if not subjects:
                print("No subjects found")
                return results
            
            print(f"Found {len(subjects)} subjects")
            
            # Limit subjects if specified
            if max_subjects:
                subjects = subjects[:max_subjects]
                print(f"Processing first {max_subjects} subjects")
            
            # Find search button
            search_button_selector = find_search_button(page)
            if not search_button_selector:
                print("Could not find search button")
                return results
            
            print(f"Found search button: {search_button_selector}")
            
            # Track processed subjects/courses to avoid duplicates
            processed_courses = {
                (desc.get("subject", ""), desc.get("course_id", ""))
                for desc in results["descriptions"]
            }
            
            # Count courses per subject from existing data to determine if subject is complete
            courses_per_subject = {}
            for desc in results["descriptions"]:
                subj = desc.get("subject", "")
                if subj:
                    courses_per_subject[subj] = courses_per_subject.get(subj, 0) + 1
            
            # Process each subject
            subjects_processed_count = 0
            for idx, subject in enumerate(subjects, 1):
                subject_code = subject.get("value", "")
                subject_label = subject.get("label", "")
                
                # Skip if subject is already completed
                if subject_code in completed_subjects:
                    print(f"\n[{idx}/{len(subjects)}] ⏭ Skipping completed subject: {subject_label} ({subject_code})")
                    continue
                
                subjects_processed_count += 1
                
                # Take a break after every N subjects (count only processed subjects)
                if subjects_processed_count > 1 and (subjects_processed_count - 1) % break_after_subjects == 0:
                    print(f"\n⏸ Taking a {break_duration}s break after {subjects_processed_count - 1} subjects...")
                    random_delay(break_duration * 0.9, break_duration * 1.1)
                
                print(f"\n[{idx}/{len(subjects)}] Processing subject: {subject_label} ({subject_code})")
                
                # Delay before processing subject (except first one)
                if idx > 1:
                    random_delay(
                        delay_between_subjects * 0.8,
                        delay_between_subjects * 1.2
                    )
                
                # Navigate back to search page if not already there
                if "cdm.woa" not in page.url or "0.3.10.21" not in page.url:
                    print("Navigating back to search page...")
                    navigate_with_retry(page, SEARCH_URL)
                    wait_for_page_load(page)
                    random_delay(delay_between_actions * 0.8, delay_between_actions * 1.2)
                
                # Select subject
                if not safe_select_option(page, subject_selector, subject_code, wait_after=delay_between_actions):
                    print(f"Failed to select subject {subject_code}")
                    continue
                
                # Click search button
                if not safe_click(page, search_button_selector, wait_after=delay_between_actions * 2):
                    print(f"Failed to click search button for {subject_code}")
                    continue
                
                # Wait for results page
                wait_for_page_load(page, timeout=20000)
                random_delay(delay_between_actions * 0.8, delay_between_actions * 1.2)
                
                # Extract course links
                courses = extract_course_info_from_results(page)
                if not courses:
                    print(f"No courses found for {subject_code}")
                    continue
                
                print(f"Found {len(courses)} courses for {subject_code}")
                
                # Limit courses if specified
                if max_courses_per_subject:
                    courses = courses[:max_courses_per_subject]
                    print(f"Processing first {max_courses_per_subject} courses")
                
                # Store the results page URL for navigation back
                results_page_url = page.url
                
                # Process each course
                for course_idx, course in enumerate(courses, 1):
                    course_id = course.get("course_id", "")
                    course_title = course.get("course_title", "")
                    link_url = course.get("link_url", "")
                    
                    # Skip if already processed
                    course_key = (subject_code, course_id)
                    if course_key in processed_courses:
                        print(f"  [{course_idx}/{len(courses)}] Skipping (already processed): {course_id} - {course_title}")
                        continue
                    
                    print(f"  [{course_idx}/{len(courses)}] Processing: {course_id} - {course_title}")
                    
                    # Delay before processing course (except first one)
                    if course_idx > 1:
                        random_delay(
                            delay_between_courses * 0.7,
                            delay_between_courses * 1.3
                        )
                    
                    try:
                        # Make sure we're on the results page
                        if page.url != results_page_url:
                            navigate_with_retry(page, results_page_url, max_retries=2)
                            wait_for_page_load(page)
                            random_delay(delay_between_actions * 0.8, delay_between_actions * 1.2)
                        
                        # Find and click the course link
                        links = page.query_selector_all(COURSE_SCHEDULE_LINK_SELECTOR)
                        if course_idx <= len(links):
                            # Click the link
                            links[course_idx - 1].click()
                            wait_for_page_load(page, timeout=20000)
                        elif link_url:
                            # Fallback: navigate directly to the URL if link not found
                            navigate_with_retry(page, link_url, max_retries=2)
                        else:
                            print(f"    ✗ Could not find course link")
                            results["metadata"]["failed_courses"] += 1
                            continue
                        
                        random_delay(delay_between_actions * 0.8, delay_between_actions * 1.2)
                        
                        # Extract description
                        description = extract_course_description(page)
                        
                        if description:
                            results["descriptions"].append({
                                "subject": subject_code,
                                "subject_label": subject_label,
                                "course_id": course_id,
                                "course_title": course_title,
                                "description": description,
                                "url": page.url
                            })
                            processed_courses.add(course_key)
                            results["metadata"]["successful_courses"] += 1
                            print(f"    ✓ Extracted description ({len(description)} chars)")
                        else:
                            print(f"    ✗ Could not extract description")
                            results["metadata"]["failed_courses"] += 1
                        
                        # Go back to results page
                        try:
                            page.go_back()
                            wait_for_page_load(page)
                        except Exception:
                            # If go_back fails, navigate directly to results page URL
                            navigate_with_retry(page, results_page_url, max_retries=2)
                            wait_for_page_load(page)
                        random_delay(delay_between_actions * 0.5, delay_between_actions * 1.0)
                        
                    except Exception as e:
                        print(f"    ✗ Error processing course: {e}")
                        results["metadata"]["failed_courses"] += 1
                        # Try to go back to results page
                        try:
                            page.go_back()
                            wait_for_page_load(page)
                        except Exception:
                            # If going back fails, navigate to results page URL
                            try:
                                navigate_with_retry(page, results_page_url, max_retries=2)
                                wait_for_page_load(page)
                            except Exception:
                                # Last resort: navigate to search page
                                navigate_with_retry(page, SEARCH_URL)
                                wait_for_page_load(page)
                        random_delay(delay_between_actions * 0.8, delay_between_actions * 1.2)
                
                # Check if all courses in this subject have been processed
                courses_in_subject = [
                    c for c in courses 
                    if (subject_code, c.get("course_id", "")) not in processed_courses
                ]
                
                # If no remaining courses to process, mark subject as completed
                if not courses_in_subject:
                    if subject_code not in completed_subjects:
                        completed_subjects.add(subject_code)
                        results["metadata"]["completed_subjects"] = sorted(completed_subjects)
                        print(f"  ✓ Subject {subject_code} fully completed (all courses processed)")
                
                results["metadata"]["total_courses"] += len(courses)
                results["metadata"]["completed_subjects"] = sorted(completed_subjects)
                
                # Save progress after every subject (save_progress_every=1)
                results["metadata"]["last_updated"] = datetime.now().isoformat()
                results["metadata"]["total_subjects"] = subjects_processed_count
                if progress_file:
                    progress_file.parent.mkdir(parents=True, exist_ok=True)
                    progress_file.write_text(
                        json.dumps(results, indent=2, ensure_ascii=False),
                        encoding="utf-8"
                    )
                    print(f"\n💾 Progress saved: {len(results['descriptions'])} descriptions, {len(completed_subjects)} subjects completed")
            
            results["metadata"]["total_subjects"] = subjects_processed_count
            results["metadata"]["completed_subjects"] = sorted(completed_subjects)
            
        except Exception as e:
            print(f"Fatal error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            context.close()
            browser.close()
    
    return results


def main():
    """Main entry point for the scraper."""
    scraping_dir = Path(__file__).resolve().parents[1]
    data_path = scraping_dir / "data" / "course_descriptions.json"
    progress_path = scraping_dir / "data" / "course_descriptions_progress.json"
    
    print("=" * 70)
    print("YORK UNIVERSITY COURSE DESCRIPTION SCRAPER")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    print("Rate limiting settings:")
    print("  - Delay between actions: 2-3 seconds (randomized)")
    print("  - Delay between courses: 3-4 seconds (randomized)")
    print("  - Delay between subjects: 5-6 seconds (randomized)")
    print("  - Break after every 10 subjects: 60 seconds")
    print("  - Progress saved every 1 subject\n")
    
    # For testing, you can limit subjects and courses
    # Remove these limits for full scraping
    # Recommended settings to avoid rate limiting:
    results = scrape_course_descriptions(
        headless=True,
        max_subjects=None,  # Set to a number (e.g., 5) for testing
        max_courses_per_subject=None,  # Set to a number (e.g., 3) for testing
        delay_between_actions=2.0,  # Base delay between actions (randomized ±20%)
        delay_between_courses=3.0,  # Delay between courses (randomized ±30%)
        delay_between_subjects=5.0,  # Delay between subjects (randomized ±20%)
        break_after_subjects=10,  # Take a break after every 10 subjects
        break_duration=60.0,  # 60 second break
        save_progress_every=1,  # Save progress every 1 subject
        progress_file=progress_path  # Save incremental progress
    )
    
    # Save results
    data_path.parent.mkdir(parents=True, exist_ok=True)
    data_path.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total subjects processed: {results['metadata']['total_subjects']}")
    print(f"Total courses found: {results['metadata']['total_courses']}")
    print(f"Successful extractions: {results['metadata']['successful_courses']}")
    print(f"Failed extractions: {results['metadata']['failed_courses']}")
    print(f"Saved to: {data_path}")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")


if __name__ == "__main__":
    main()
