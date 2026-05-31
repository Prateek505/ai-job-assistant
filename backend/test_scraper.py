"""
Test script for Playwright job scraper.
Run this to verify scraping functionality works properly.

Usage:
    python test_scraper.py
"""

import asyncio
import sys
import os

# Fix encoding issues on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, ".")

from app.services.job_scraper import scrape_greenhouse, scrape_lever, scrape_career_page


async def test_greenhouse():
    """Test Greenhouse scraper."""
    print("\n" + "="*60)
    print("Testing Greenhouse Scraper")
    print("="*60)

    company = "figma"
    print(f"\nScraping Greenhouse for: {company}")

    jobs = await scrape_greenhouse(company)

    print(f"\n[OK] Found {len(jobs)} jobs from {company}")
    if jobs:
        print("\nSample job:")
        job = jobs[0]
        print(f"  Title: {job.title}")
        print(f"  Company: {job.company}")
        print(f"  Location: {job.location}")
        print(f"  Link: {job.application_link[:80]}...")
        print(f"  Description: {job.description[:100]}...")


async def test_lever():
    """Test Lever scraper."""
    print("\n" + "="*60)
    print("Testing Lever Scraper")
    print("="*60)

    company = "netflix"
    print(f"\nScraping Lever for: {company}")

    jobs = await scrape_lever(company)

    print(f"\n✅ Found {len(jobs)} jobs from {company}")
    if jobs:
        print("\nSample job:")
        job = jobs[0]
        print(f"  Title: {job.title}")
        print(f"  Company: {job.company}")
        print(f"  Location: {job.location}")
        print(f"  Link: {job.application_link[:80]}...")


async def test_career_page():
    """Test generic career page scraper with Playwright."""
    print("\n" + "="*60)
    print("Testing Generic Career Page Scraper (Playwright)")
    print("="*60)

    url = "https://boards.greenhouse.io/figma"  # Using Greenhouse as a test
    company = "Figma"
    print(f"\nScraping career page: {url}")
    print("Note: This uses Playwright to render JavaScript and find job links\n")

    jobs = await scrape_career_page(url, company)

    print(f"\n✅ Found {len(jobs)} jobs from {company}")
    if jobs:
        print("\nSample jobs:")
        for i, job in enumerate(jobs[:3], 1):
            print(f"\n  Job {i}:")
            print(f"    Title: {job.title}")
            print(f"    Link: {job.application_link[:80]}...")


async def main():
    """Run all scraper tests."""
    print("\n[*] Starting Playwright Job Scraper Tests")
    print("This will test all three scraping methods:\n")

    try:
        # Test Greenhouse (API-based, fast)
        await test_greenhouse()

        # Test Lever (API-based, fast)
        await test_lever()

        # Test Career Page (Playwright-based, slower)
        await test_career_page()

        print("\n" + "="*60)
        print("[OK] All scraper tests completed successfully!")
        print("="*60)
        print("\nNext steps:")
        print("1. Start the backend: uvicorn app.main:app --reload")
        print("2. Test scraping via API: POST http://localhost:8000/api/scraping/greenhouse")
        print("3. Use the frontend scraping page to manually trigger scrapes")

    except Exception as e:
        print(f"\n[ERROR] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
