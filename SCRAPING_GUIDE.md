# Job Scraping Feature - Implementation Guide

## Overview

The Playwright job scraping feature has been fully implemented to automatically discover and import job listings from various career pages.

## What's Implemented

### Backend (Python/FastAPI)

1. **Enhanced job_scraper.py service** (`backend/app/services/job_scraper.py`)
   - ✅ Greenhouse API scraper (fast, JSON-based)
   - ✅ Lever API scraper (fast, JSON-based)
   - ✅ Generic career page scraper with Playwright (browser-based, JavaScript support)
   - ✅ Database integration with deduplication
   - ✅ Improved error handling and logging
   - ✅ Better selector patterns for finding job listings
   - ✅ Location and description extraction

2. **New Scraping API Router** (`backend/app/routers/scraping_router.py`)
   - ✅ POST `/api/scraping/greenhouse` - Scrape Greenhouse boards
   - ✅ POST `/api/scraping/lever` - Scrape Lever boards
   - ✅ POST `/api/scraping/career-page` - Scrape any career page with Playwright
   - ✅ POST `/api/scraping/batch` - Batch scraping (background tasks)
   - ✅ GET `/api/scraping/status` - Get scraping status and config

3. **Updated Celery Tasks** (`backend/app/tasks.py`)
   - ✅ Automatic hourly scraping with database saving
   - ✅ Proper stats tracking (new, updated, skipped jobs)
   - ✅ Better error handling and logging

### Frontend (React/TypeScript)

1. **New Scraping Page** (`frontend/src/pages/ScrapingPage.tsx`)
   - ✅ Tabbed interface for Greenhouse, Lever, and Career Page scrapers
   - ✅ Form validation and user-friendly inputs
   - ✅ Real-time feedback with toast notifications
   - ✅ Results display showing stats (new, updated, skipped jobs)
   - ✅ Clean, modern UI with proper styling

2. **Updated Navigation**
   - ✅ Added "Job Scraping" to sidebar menu
   - ✅ Proper routing with authentication protection

## Installation & Setup

### 1. Install Dependencies

Playwright is already in `requirements.txt`, but you need to install browser binaries:

```bash
cd backend
pip install playwright
python -m playwright install chromium
```

### 2. Verify Installation

Run the test script:

```bash
cd backend
python test_scraper.py
```

This will test all three scraping methods and show sample results.

### 3. Start the Backend

```bash
cd backend
uvicorn app.main:app --reload
```

The scraping API will be available at `http://localhost:8000/api/scraping`

### 4. Start the Frontend

```bash
cd frontend
npm run dev
```

Access the scraping page at `http://localhost:5173/scraping`

## Usage

### Via Web Interface

1. Log in to the application
2. Navigate to "Job Scraping" in the sidebar
3. Select a scraper type (Greenhouse, Lever, or Career Page)
4. Enter the required information:
   - **Greenhouse**: Company slug (e.g., "figma", "notion")
   - **Lever**: Company slug (e.g., "netflix", "stripe")
   - **Career Page**: Full URL + company name
5. Click "Scrape" and view results

### Via API (cURL)

**Scrape Greenhouse:**
```bash
curl -X POST http://localhost:8000/api/scraping/greenhouse \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"company_slug": "figma"}'
```

**Scrape Lever:**
```bash
curl -X POST http://localhost:8000/api/scraping/lever \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"company_slug": "netflix"}'
```

**Scrape Career Page:**
```bash
curl -X POST http://localhost:8000/api/scraping/career-page \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/careers",
    "company_name": "Example Corp"
  }'
```

**Batch Scraping:**
```bash
curl -X POST http://localhost:8000/api/scraping/batch \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "greenhouse_companies": ["figma", "notion"],
    "lever_companies": ["netflix"],
    "career_pages": [
      {"url": "https://example.com/careers", "company_name": "Example"}
    ]
  }'
```

### Via Celery (Automated)

The Celery task automatically runs every hour:

```bash
cd backend
celery -A app.tasks worker -l info
```

To schedule periodic scraping:
```bash
celery -A app.tasks beat -l info
```

## Features

### Deduplication

Jobs are deduplicated based on:
- Title + Company + Application URL

Existing jobs are updated if:
- Description changes
- Location changes

### Error Handling

- Network errors are caught and logged
- Partial failures don't stop batch scraping
- Detailed error messages in API responses
- Graceful fallback for missing data

### Playwright Features

The career page scraper includes:
- Multiple selector patterns to find job listings
- JavaScript rendering support
- Dynamic content waiting
- Link normalization
- Location extraction from parent elements
- Duplicate link filtering
- User-agent spoofing to avoid bot detection

### Performance

- **Greenhouse/Lever**: ~1-3 seconds (API-based)
- **Career Page**: ~5-10 seconds (Playwright, depends on page complexity)
- Background processing available for batch operations

## Troubleshooting

### "Module 'playwright' not found"

```bash
pip install playwright
```

### "Browser not found"

```bash
python -m playwright install chromium
```

### "Timeout waiting for page to load"

Increase timeout in `job_scraper.py`:
```python
await page.goto(url, wait_until="domcontentloaded", timeout=60000)  # 60 seconds
```

### "No jobs found"

1. Check if the URL is correct
2. Try different selector patterns in `scrape_career_page()` function
3. Inspect the page manually to find job listing selectors
4. Some career pages may require authentication or have anti-scraping measures

### Playwright in Production

For production deployment on Linux servers, you may need additional dependencies:

```bash
playwright install-deps chromium
```

Or use Docker with pre-installed browsers.

## API Documentation

Full API docs available at: `http://localhost:8000/docs`

## Next Steps

1. **Add more company configurations**: Edit `tasks.py` to add more companies to scan
2. **Schedule custom scraping intervals**: Modify Celery beat schedule
3. **Add webhook notifications**: Get notified when new jobs are found
4. **Implement job filtering**: Filter jobs by keywords before saving
5. **Add scraping history**: Track when companies were last scraped
6. **Custom selectors per company**: Store custom CSS selectors for problematic sites

## Architecture

```
User Request → FastAPI Router → Scraper Service → Database
                                      ↓
                               Playwright Browser
                                      ↓
                              Career Page (HTML)
```

## Security Notes

- All scraping endpoints require authentication
- Rate limiting recommended for production
- Respect robots.txt and terms of service
- Use appropriate user-agent headers
- Consider legal implications of web scraping

---

**Implementation Status**: ✅ Complete and tested
**Date**: 2026-03-24
