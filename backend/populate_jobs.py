"""
Script to populate the database with real jobs from various companies.
Run this once to get initial jobs into the system.

Usage:
    python populate_jobs.py
"""

import asyncio
import sys

# Fix encoding issues on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, ".")


async def populate_jobs():
    """Scrape jobs from multiple companies and save to database."""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.config import settings
    from app.services.job_scraper import scrape_and_save

    print("=" * 60)
    print("JOB DATABASE POPULATION SCRIPT")
    print("=" * 60)
    print("\nThis will scrape real jobs from top tech companies.\n")

    # Create async engine and session
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    # Companies to scrape - using a focused list for faster initial population
    greenhouse_companies = [
        # AI/ML Companies (high demand)
        "openai", "anthropic", "cohere", "huggingface", "scale",
        # High-Growth Startups
        "figma", "notion", "vercel", "stripe", "databricks",
        "airtable", "linear", "retool", "webflow", "loom",
        # Fintech
        "plaid", "brex", "ramp", "coinbase",
        # Developer Tools
        "github", "gitlab", "hashicorp", "datadog", "snyk",
        # Cloud & Infrastructure
        "cloudflare", "render", "supabase", "planetscale",
    ]

    lever_companies = [
        "netflix", "canva", "robinhood", "chime",
        "twilio", "okta", "elastic", "mongodb",
        "segment", "amplitude", "asana", "dropbox",
    ]

    total_stats = {
        "total_scraped": 0,
        "new_jobs": 0,
        "updated_jobs": 0,
        "skipped_jobs": 0,
        "errors": 0
    }

    async with async_session() as db:
        # Scrape Greenhouse companies
        print("\n[GREENHOUSE COMPANIES]")
        print("-" * 40)
        for i, slug in enumerate(greenhouse_companies, 1):
            print(f"[{i}/{len(greenhouse_companies)}] Scraping {slug}...", end=" ")
            try:
                result = await scrape_and_save("greenhouse", slug, db)
                if result.get("success"):
                    jobs_found = result.get("jobs_found", 0)
                    new_jobs = result.get("new_jobs", 0)
                    total_stats["total_scraped"] += jobs_found
                    total_stats["new_jobs"] += new_jobs
                    total_stats["updated_jobs"] += result.get("updated_jobs", 0)
                    total_stats["skipped_jobs"] += result.get("skipped_jobs", 0)
                    print(f"Found {jobs_found} jobs, {new_jobs} new")
                else:
                    print(f"Failed: {result.get('message', 'Unknown error')}")
                    total_stats["errors"] += 1
            except Exception as e:
                print(f"Error: {str(e)[:50]}")
                total_stats["errors"] += 1

        # Scrape Lever companies
        print("\n[LEVER COMPANIES]")
        print("-" * 40)
        for i, slug in enumerate(lever_companies, 1):
            print(f"[{i}/{len(lever_companies)}] Scraping {slug}...", end=" ")
            try:
                result = await scrape_and_save("lever", slug, db)
                if result.get("success"):
                    jobs_found = result.get("jobs_found", 0)
                    new_jobs = result.get("new_jobs", 0)
                    total_stats["total_scraped"] += jobs_found
                    total_stats["new_jobs"] += new_jobs
                    total_stats["updated_jobs"] += result.get("updated_jobs", 0)
                    total_stats["skipped_jobs"] += result.get("skipped_jobs", 0)
                    print(f"Found {jobs_found} jobs, {new_jobs} new")
                else:
                    print(f"Failed: {result.get('message', 'Unknown error')}")
                    total_stats["errors"] += 1
            except Exception as e:
                print(f"Error: {str(e)[:50]}")
                total_stats["errors"] += 1

    await engine.dispose()

    # Print summary
    print("\n" + "=" * 60)
    print("POPULATION COMPLETE!")
    print("=" * 60)
    print(f"\nTotal jobs scraped:  {total_stats['total_scraped']}")
    print(f"New jobs added:      {total_stats['new_jobs']}")
    print(f"Jobs updated:        {total_stats['updated_jobs']}")
    print(f"Jobs skipped:        {total_stats['skipped_jobs']}")
    print(f"Errors:              {total_stats['errors']}")
    print("\nJobs are now available in the Job Feed!")
    print("Visit http://localhost:5175/jobs to see them.")

    return total_stats


if __name__ == "__main__":
    print("\nStarting job population...\n")
    asyncio.run(populate_jobs())
