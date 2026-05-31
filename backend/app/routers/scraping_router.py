"""
Scraping router — API endpoints to trigger job scraping manually.
Supports Greenhouse, Lever, and generic career pages.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db, async_session
from ..models import User
from ..auth import get_current_user
from ..services.job_scraper import (
    scrape_and_save, scrape_greenhouse, scrape_lever, scrape_career_page,
    scrape_linkedin, scrape_naukri, scrape_indeed, scrape_glassdoor,
    scrape_remoteok, scrape_arbeitnow, scrape_ashby, scrape_smartrecruiters,
    scrape_bamboohr, scrape_workable, scrape_jazzhr, scrape_workday,
)

router = APIRouter()


# ── Request/Response Schemas ──────────────────────────────────

class ScrapeGreenhouseRequest(BaseModel):
    company_slug: str


class ScrapeLeverRequest(BaseModel):
    company_slug: str


class ScrapeCareerPageRequest(BaseModel):
    url: HttpUrl
    company_name: str


class ScrapeJobBoardRequest(BaseModel):
    """For keyword-based job boards: LinkedIn, Naukri, Indeed, Glassdoor, RemoteOK, Arbeitnow."""
    keywords: str
    location: str = ""


class ScrapeATSRequest(BaseModel):
    """For ATS platforms: Ashby, SmartRecruiters, BambooHR, Workable, JazzHR, Workday."""
    company_slug: str


class BatchScrapeRequest(BaseModel):
    greenhouse_companies: List[str] = []
    lever_companies: List[str] = []
    career_pages: List[dict] = []  # [{"url": "...", "company_name": "..."}]


class ScrapeResponse(BaseModel):
    success: bool
    message: str
    scraper_type: str
    jobs_found: int
    new_jobs: int = 0
    updated_jobs: int = 0
    skipped_jobs: int = 0
    error: Optional[str] = None


# ── API Endpoints ─────────────────────────────────────────────

@router.post("/greenhouse", response_model=ScrapeResponse)
async def scrape_greenhouse_endpoint(
    body: ScrapeGreenhouseRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Scrape jobs from a Greenhouse career board.
    Example: {"company_slug": "figma"}
    """
    result = await scrape_and_save("greenhouse", body.company_slug, db)
    return result


@router.post("/lever", response_model=ScrapeResponse)
async def scrape_lever_endpoint(
    body: ScrapeLeverRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Scrape jobs from a Lever career board.
    Example: {"company_slug": "netflix"}
    """
    result = await scrape_and_save("lever", body.company_slug, db)
    return result


@router.post("/career-page", response_model=ScrapeResponse)
async def scrape_career_page_endpoint(
    body: ScrapeCareerPageRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Scrape jobs from a generic career page using Playwright.
    Example: {"url": "https://example.com/careers", "company_name": "Example Corp"}
    """
    result = await scrape_and_save(
        "career_page",
        body.company_name,
        db,
        custom_url=str(body.url)
    )
    return result


# ── Job Board Scrapers (keyword-based) ────────────────────────

@router.post("/linkedin", response_model=ScrapeResponse)
async def scrape_linkedin_endpoint(
    body: ScrapeJobBoardRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Scrape public LinkedIn job listings. keywords='software engineer', location='United States'"""
    result = await scrape_and_save("linkedin", body.keywords, db, custom_url=body.location)
    return result


@router.post("/naukri", response_model=ScrapeResponse)
async def scrape_naukri_endpoint(
    body: ScrapeJobBoardRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Scrape Naukri.com job listings. keywords='python developer', location='bangalore'"""
    result = await scrape_and_save("naukri", body.keywords, db, custom_url=body.location)
    return result


@router.post("/indeed", response_model=ScrapeResponse)
async def scrape_indeed_endpoint(
    body: ScrapeJobBoardRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Scrape Indeed.com job listings. keywords='data scientist', location='New York'"""
    result = await scrape_and_save("indeed", body.keywords, db, custom_url=body.location)
    return result


@router.post("/glassdoor", response_model=ScrapeResponse)
async def scrape_glassdoor_endpoint(
    body: ScrapeJobBoardRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Scrape Glassdoor job listings. keywords='product manager'"""
    result = await scrape_and_save("glassdoor", body.keywords, db, custom_url=body.location)
    return result


@router.post("/remoteok", response_model=ScrapeResponse)
async def scrape_remoteok_endpoint(
    body: ScrapeJobBoardRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Scrape RemoteOK.com remote jobs. keywords='react' (optional)"""
    result = await scrape_and_save("remoteok", body.keywords, db)
    return result


@router.post("/arbeitnow", response_model=ScrapeResponse)
async def scrape_arbeitnow_endpoint(
    body: ScrapeJobBoardRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Scrape Arbeitnow.com EU/remote jobs. keywords='backend' (optional)"""
    result = await scrape_and_save("arbeitnow", body.keywords, db)
    return result


# ── ATS Platform Scrapers (company slug-based) ───────────────

@router.post("/ashby", response_model=ScrapeResponse)
async def scrape_ashby_endpoint(
    body: ScrapeATSRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Scrape Ashby ATS job board. company_slug='ramp'"""
    result = await scrape_and_save("ashby", body.company_slug, db)
    return result


@router.post("/smartrecruiters", response_model=ScrapeResponse)
async def scrape_smartrecruiters_endpoint(
    body: ScrapeATSRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Scrape SmartRecruiters company jobs. company_slug='Visa'"""
    result = await scrape_and_save("smartrecruiters", body.company_slug, db)
    return result


@router.post("/bamboohr", response_model=ScrapeResponse)
async def scrape_bamboohr_endpoint(
    body: ScrapeATSRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Scrape BambooHR career boards. company_slug='samsara'"""
    result = await scrape_and_save("bamboohr", body.company_slug, db)
    return result


@router.post("/workable", response_model=ScrapeResponse)
async def scrape_workable_endpoint(
    body: ScrapeATSRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Scrape Workable ATS. company_slug='posthog'"""
    result = await scrape_and_save("workable", body.company_slug, db)
    return result


@router.post("/jazzhr", response_model=ScrapeResponse)
async def scrape_jazzhr_endpoint(
    body: ScrapeATSRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Scrape JazzHR. company_slug='company-id'"""
    result = await scrape_and_save("jazzhr", body.company_slug, db)
    return result


@router.post("/workday", response_model=ScrapeResponse)
async def scrape_workday_endpoint(
    body: ScrapeATSRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Scrape Workday career sites. company_slug='salesforce'"""
    result = await scrape_and_save("workday", body.company_slug, db)
    return result


@router.post("/batch")
async def batch_scrape_endpoint(
    body: BatchScrapeRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
):
    """
    Trigger batch scraping for multiple companies in the background.
    Returns immediately and processes scraping asynchronously.
    """
    total_requested = (
        len(body.greenhouse_companies) +
        len(body.lever_companies) +
        len(body.career_pages)
    )

    if total_requested == 0:
        raise HTTPException(status_code=400, detail="No companies provided")

    async def _bg_scrape(scraper_type: str, identifier: str, custom_url: str | None = None):
        """Run scrape_and_save with its own DB session (request session is closed)."""
        async with async_session() as db:
            try:
                await scrape_and_save(scraper_type, identifier, db, custom_url)
                await db.commit()
            except Exception:
                await db.rollback()

    # Add scraping tasks to background
    for slug in body.greenhouse_companies:
        background_tasks.add_task(_bg_scrape, "greenhouse", slug)

    for slug in body.lever_companies:
        background_tasks.add_task(_bg_scrape, "lever", slug)

    for page in body.career_pages:
        background_tasks.add_task(
            _bg_scrape,
            "career_page",
            page.get("company_name", "Unknown"),
            page.get("url"),
        )

    return {
        "success": True,
        "message": f"Batch scraping started for {total_requested} sources",
        "processing": "background"
    }


@router.get("/status")
async def scraping_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current scraping configuration and status.
    """
    # In production, this could show scheduled tasks, last run times, etc.
    return {
        "supported_platforms": {
            "ats_company_slug": ["greenhouse", "lever", "ashby", "smartrecruiters", "bamboohr", "workable", "jazzhr", "workday"],
            "job_boards_keyword": ["linkedin", "naukri", "indeed", "glassdoor", "remoteok", "arbeitnow"],
            "custom": ["career_page"],
        },
        "examples": {
            "greenhouse": "figma, notion, vercel, stripe, openai",
            "lever": "netflix, canva, robinhood",
            "ashby": "ramp, linear",
            "linkedin": "keywords='software engineer', location='United States'",
            "naukri": "keywords='python developer', location='bangalore'",
            "indeed": "keywords='data analyst', location='New York'",
            "remoteok": "keywords='react' (optional)",
        },
    }
