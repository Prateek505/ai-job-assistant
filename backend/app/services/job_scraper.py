"""
Job scraper — scrapes jobs from multiple platforms and career pages.
Supports: Greenhouse, Lever, LinkedIn, Naukri, Indeed, Glassdoor, RemoteOK,
           WorkDay, Ashby, SmartRecruiters, BambooHR, JazzHR,
           and generic career pages via Playwright.

NOTE: This is designed to be run as a Celery task or standalone script.
In the web app, it provides utility functions for parsing job listings.
"""

import asyncio
import json
import re
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, quote_plus
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)

# Common headers to mimic a real browser for HTTP-based scrapers
_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

logger = logging.getLogger(__name__)


# ── Data structure for scraped jobs ──────────────────────────

class ScrapedJob:
    def __init__(
        self,
        title: str,
        company: str,
        description: str = "",
        location: str = "",
        application_link: str = "",
        posting_date: Optional[datetime] = None,
        source: str = "web",
    ):
        self.title = title
        self.company = company
        self.description = description
        self.location = location
        self.application_link = application_link
        self.posting_date = posting_date or datetime.now(timezone.utc)
        self.source = source


# ── Greenhouse scraper ───────────────────────────────────────

async def scrape_greenhouse(company_slug: str) -> List[ScrapedJob]:
    """
    Scrape jobs from a Greenhouse career board.
    URL format: https://boards.greenhouse.io/{company_slug}
    """
    jobs = []
    url = f"https://boards-api.greenhouse.io/v1/boards/{company_slug}/jobs"

    try:
        # Use the JSON API (no browser needed)
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=15)
            if response.status_code != 200:
                logger.warning(f"Greenhouse API returned {response.status_code} for {company_slug}")
                return jobs

            data = response.json()
            for job_data in data.get("jobs", []):
                jobs.append(ScrapedJob(
                    title=job_data.get("title", ""),
                    company=company_slug.replace("-", " ").title(),
                    description=_strip_html(job_data.get("content", "")),
                    location=job_data.get("location", {}).get("name", ""),
                    application_link=job_data.get("absolute_url", ""),
                    source="greenhouse",
                ))
    except Exception as e:
        logger.error(f"Error scraping Greenhouse for {company_slug}: {e}")

    return jobs


# ── Lever scraper ────────────────────────────────────────────

async def scrape_lever(company_slug: str) -> List[ScrapedJob]:
    """
    Scrape jobs from a Lever career page.
    URL format: https://api.lever.co/v0/postings/{company_slug}
    """
    jobs = []
    url = f"https://api.lever.co/v0/postings/{company_slug}?mode=json"

    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=15)
            if response.status_code != 200:
                logger.warning(f"Lever API returned {response.status_code} for {company_slug}")
                return jobs

            data = response.json()
            for job_data in data:
                location_parts = []
                cat = job_data.get("categories", {})
                if cat.get("location"):
                    location_parts.append(cat["location"])
                if cat.get("commitment"):
                    location_parts.append(cat["commitment"])

                jobs.append(ScrapedJob(
                    title=job_data.get("text", ""),
                    company=company_slug.replace("-", " ").title(),
                    description=job_data.get("descriptionPlain", ""),
                    location=" · ".join(location_parts),
                    application_link=job_data.get("hostedUrl", ""),
                    source="lever",
                ))
    except Exception as e:
        logger.error(f"Error scraping Lever for {company_slug}: {e}")

    return jobs


# ── LinkedIn scraper (public job search — no login) ──────────

async def scrape_linkedin(keywords: str, location: str = "") -> List[ScrapedJob]:
    """
    Scrape public LinkedIn job listings via their guest job search page.
    Uses Playwright to render the JS-heavy page and extract listings.
    keywords: search terms like 'software engineer', 'data scientist'
    location: optional geo filter like 'United States', 'India'
    """
    jobs = []
    browser = None
    try:
        from playwright.async_api import async_playwright, TimeoutError as PWTimeout

        q = quote_plus(keywords)
        loc = quote_plus(location) if location else ""
        url = f"https://www.linkedin.com/jobs/search/?keywords={q}"
        if loc:
            url += f"&location={loc}"

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            ctx = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=_BROWSER_HEADERS["User-Agent"],
            )
            page = await ctx.new_page()

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            except PWTimeout:
                logger.warning(f"LinkedIn timeout for {keywords}")
                await browser.close()
                return jobs

            await page.wait_for_timeout(3000)

            # Scroll a few times to load more results
            for _ in range(3):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1500)

            cards = await page.query_selector_all(
                "div.base-card, div.job-search-card, li.jobs-search-results__list-item"
            )
            seen = set()
            for card in cards[:60]:
                try:
                    title_el = await card.query_selector(
                        "h3.base-search-card__title, h3.job-card-list__title, span.sr-only"
                    )
                    company_el = await card.query_selector(
                        "h4.base-search-card__subtitle, a.job-card-container__company-name"
                    )
                    location_el = await card.query_selector(
                        "span.job-search-card__location, span.job-card-container__metadata-item"
                    )
                    link_el = await card.query_selector(
                        "a.base-card__full-link, a.job-card-list__title"
                    )

                    title = (await title_el.inner_text()).strip() if title_el else ""
                    comp = (await company_el.inner_text()).strip() if company_el else ""
                    loc_text = (await location_el.inner_text()).strip() if location_el else ""
                    href = (await link_el.get_attribute("href") or "") if link_el else ""

                    if not title or len(title) < 3 or href in seen:
                        continue
                    seen.add(href)

                    jobs.append(ScrapedJob(
                        title=title,
                        company=comp or "Unknown",
                        location=loc_text,
                        application_link=href.split("?")[0] if href else "",
                        source="linkedin",
                    ))
                except Exception:
                    continue

            await ctx.close()
            await browser.close()
            logger.info(f"LinkedIn: scraped {len(jobs)} jobs for '{keywords}'")
    except Exception as e:
        logger.error(f"Error scraping LinkedIn for '{keywords}': {e}")
        if browser:
            try:
                await browser.close()
            except Exception:
                pass
    return jobs


# ── Naukri scraper (India's largest job portal) ──────────────

async def scrape_naukri(keywords: str, location: str = "") -> List[ScrapedJob]:
    """
    Scrape jobs from Naukri.com using their public search page.
    """
    jobs = []
    browser = None
    try:
        from playwright.async_api import async_playwright, TimeoutError as PWTimeout

        slug = keywords.lower().replace(" ", "-")
        loc_slug = location.lower().replace(" ", "-") if location else ""
        url = f"https://www.naukri.com/{slug}-jobs"
        if loc_slug:
            url += f"-in-{loc_slug}"

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            ctx = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=_BROWSER_HEADERS["User-Agent"],
            )
            page = await ctx.new_page()
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            except PWTimeout:
                logger.warning(f"Naukri timeout for {keywords}")
                await browser.close()
                return jobs

            await page.wait_for_timeout(3000)

            cards = await page.query_selector_all(
                "article.jobTuple, div.srp-jobtuple-wrapper, div.cust-job-tuple"
            )
            if not cards:
                # Fallback selectors for newer Naukri redesign
                cards = await page.query_selector_all("div.styles_jlc__main__VdwtF, div[class*='jobTuple']")

            seen = set()
            for card in cards[:50]:
                try:
                    title_el = await card.query_selector(
                        "a.title, a[class*='title'], h2 a"
                    )
                    company_el = await card.query_selector(
                        "a.subTitle, a[class*='comp-name'], span.comp-name"
                    )
                    loc_el = await card.query_selector(
                        "span.locWdth, span[class*='loc-wrap'], li.location span, span[class*='location']"
                    )
                    exp_el = await card.query_selector(
                        "span.expwdth, span[class*='exp'], li.experience span"
                    )

                    title = (await title_el.inner_text()).strip() if title_el else ""
                    href = (await title_el.get_attribute("href") or "") if title_el else ""
                    comp = (await company_el.inner_text()).strip() if company_el else ""
                    loc_text = (await loc_el.inner_text()).strip() if loc_el else ""
                    exp = (await exp_el.inner_text()).strip() if exp_el else ""

                    if not title or href in seen:
                        continue
                    seen.add(href)

                    # Ensure India is always appended to Naukri locations
                    if loc_text and "india" not in loc_text.lower():
                        loc_text = loc_text + ", India"
                    elif not loc_text:
                        loc_text = "India"

                    desc = f"Experience: {exp}" if exp else ""
                    jobs.append(ScrapedJob(
                        title=title,
                        company=comp or "Unknown",
                        location=loc_text,
                        description=desc,
                        application_link=href,
                        source="naukri",
                    ))
                except Exception:
                    continue

            await ctx.close()
            await browser.close()
            logger.info(f"Naukri: scraped {len(jobs)} jobs for '{keywords}'")
    except Exception as e:
        logger.error(f"Error scraping Naukri for '{keywords}': {e}")
        if browser:
            try:
                await browser.close()
            except Exception:
                pass
    return jobs


# ── Indeed scraper (global job board) ────────────────────────

async def scrape_indeed(keywords: str, location: str = "") -> List[ScrapedJob]:
    """
    Scrape jobs from Indeed.com using their public search page.
    """
    jobs = []
    browser = None
    try:
        from playwright.async_api import async_playwright, TimeoutError as PWTimeout

        q = quote_plus(keywords)
        loc = quote_plus(location) if location else ""
        url = f"https://www.indeed.com/jobs?q={q}"
        if loc:
            url += f"&l={loc}"

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            ctx = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=_BROWSER_HEADERS["User-Agent"],
            )
            page = await ctx.new_page()
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            except PWTimeout:
                logger.warning(f"Indeed timeout for {keywords}")
                await browser.close()
                return jobs

            await page.wait_for_timeout(3000)

            cards = await page.query_selector_all(
                "div.job_seen_beacon, div.jobsearch-ResultsList > div, td.resultContent"
            )
            seen = set()
            for card in cards[:50]:
                try:
                    title_el = await card.query_selector(
                        "h2.jobTitle a, a[data-jk], h2 span[title]"
                    )
                    company_el = await card.query_selector(
                        "span[data-testid='company-name'], span.companyName, span.company"
                    )
                    loc_el = await card.query_selector(
                        "div[data-testid='text-location'], div.companyLocation, span.companyLocation"
                    )

                    if title_el:
                        title = (await title_el.inner_text()).strip()
                        href = await title_el.get_attribute("href") or ""
                    else:
                        continue

                    comp = (await company_el.inner_text()).strip() if company_el else ""
                    loc_text = (await loc_el.inner_text()).strip() if loc_el else ""

                    if not title or href in seen:
                        continue
                    seen.add(href)

                    if href and not href.startswith("http"):
                        href = urljoin("https://www.indeed.com", href)

                    jobs.append(ScrapedJob(
                        title=title,
                        company=comp or "Unknown",
                        location=loc_text,
                        application_link=href,
                        source="indeed",
                    ))
                except Exception:
                    continue

            await ctx.close()
            await browser.close()
            logger.info(f"Indeed: scraped {len(jobs)} jobs for '{keywords}'")
    except Exception as e:
        logger.error(f"Error scraping Indeed for '{keywords}': {e}")
        if browser:
            try:
                await browser.close()
            except Exception:
                pass
    return jobs


# ── Glassdoor scraper ────────────────────────────────────────

async def scrape_glassdoor(keywords: str, location: str = "") -> List[ScrapedJob]:
    """
    Scrape jobs from Glassdoor using their public search page.
    """
    jobs = []
    browser = None
    try:
        from playwright.async_api import async_playwright, TimeoutError as PWTimeout

        q = quote_plus(keywords)
        url = f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={q}"

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            ctx = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=_BROWSER_HEADERS["User-Agent"],
            )
            page = await ctx.new_page()
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            except PWTimeout:
                logger.warning(f"Glassdoor timeout for {keywords}")
                await browser.close()
                return jobs

            await page.wait_for_timeout(3000)

            cards = await page.query_selector_all(
                "li.JobsList_jobListItem__wjTHv, li[data-test='jobListing'], div.JobCard_jobCard__rjBkS"
            )
            if not cards:
                cards = await page.query_selector_all("a[data-test='job-link'], li[class*='jobListItem']")

            seen = set()
            for card in cards[:50]:
                try:
                    title_el = await card.query_selector(
                        "a[data-test='job-link'], a.JobCard_jobTitle__GLyJ1, a[class*='jobTitle']"
                    )
                    company_el = await card.query_selector(
                        "span.EmployerProfile_compactEmployerName__9MGcV, span[class*='employerName'], div.job-search-key-1mn4rg3"
                    )
                    loc_el = await card.query_selector(
                        "div[data-test='emp-location'], span[class*='location'], div[class*='location']"
                    )

                    title = (await title_el.inner_text()).strip() if title_el else ""
                    href = (await title_el.get_attribute("href") or "") if title_el else ""
                    comp = (await company_el.inner_text()).strip() if company_el else ""
                    loc_text = (await loc_el.inner_text()).strip() if loc_el else ""

                    if not title or href in seen:
                        continue
                    seen.add(href)

                    if href and not href.startswith("http"):
                        href = urljoin("https://www.glassdoor.com", href)

                    jobs.append(ScrapedJob(
                        title=title,
                        company=comp or "Unknown",
                        location=loc_text,
                        application_link=href,
                        source="glassdoor",
                    ))
                except Exception:
                    continue

            await ctx.close()
            await browser.close()
            logger.info(f"Glassdoor: scraped {len(jobs)} jobs for '{keywords}'")
    except Exception as e:
        logger.error(f"Error scraping Glassdoor for '{keywords}': {e}")
        if browser:
            try:
                await browser.close()
            except Exception:
                pass
    return jobs


# ── RemoteOK scraper (remote jobs — JSON API) ───────────────

async def scrape_remoteok(keywords: str = "") -> List[ScrapedJob]:
    """
    Scrape remote jobs from RemoteOK.com via their public JSON API.
    """
    jobs = []
    url = "https://remoteok.com/api"
    if keywords:
        tag = keywords.lower().replace(" ", "-")
        url = f"https://remoteok.com/api?tag={tag}"

    try:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=_BROWSER_HEADERS, timeout=15)
            if resp.status_code != 200:
                logger.warning(f"RemoteOK returned {resp.status_code}")
                return jobs

            data = resp.json()
            # First element is metadata — skip it
            for item in data[1:61]:
                title = item.get("position", "")
                if not title:
                    continue
                jobs.append(ScrapedJob(
                    title=title,
                    company=item.get("company", "Unknown"),
                    description=_strip_html(item.get("description", "")),
                    location="Remote",
                    application_link=item.get("url", ""),
                    source="remoteok",
                ))
    except Exception as e:
        logger.error(f"Error scraping RemoteOK: {e}")
    return jobs


# ── Arbeitnow scraper (EU/Remote jobs — JSON API) ───────────

async def scrape_arbeitnow(keywords: str = "") -> List[ScrapedJob]:
    """
    Scrape jobs from Arbeitnow.com (European & remote jobs) via public JSON API.
    """
    jobs = []
    url = "https://www.arbeitnow.com/api/job-board-api"
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=15)
            if resp.status_code != 200:
                logger.warning(f"Arbeitnow returned {resp.status_code}")
                return jobs

            data = resp.json()
            kw_lower = keywords.lower() if keywords else ""
            for item in data.get("data", [])[:80]:
                title = item.get("title", "")
                if not title:
                    continue
                # Filter by keyword if provided
                if kw_lower and kw_lower not in title.lower() and kw_lower not in (item.get("description", "") or "").lower():
                    continue

                jobs.append(ScrapedJob(
                    title=title,
                    company=item.get("company_name", "Unknown"),
                    description=_strip_html(item.get("description", "")),
                    location=item.get("location", ""),
                    application_link=item.get("url", ""),
                    source="arbeitnow",
                ))
    except Exception as e:
        logger.error(f"Error scraping Arbeitnow: {e}")
    return jobs


# ── Ashby scraper (modern ATS — JSON API) ───────────────────

async def scrape_ashby(company_slug: str) -> List[ScrapedJob]:
    """
    Scrape jobs from Ashby ATS job boards.
    URL: https://jobs.ashbyhq.com/{company_slug}
    Uses their internal GraphQL-like API.
    """
    jobs = []
    url = f"https://jobs.ashbyhq.com/api/non-user-graphql?op=ApiJobBoardWithTeams"
    payload = {
        "operationName": "ApiJobBoardWithTeams",
        "variables": {"organizationHostedJobsPageName": company_slug},
        "query": (
            "query ApiJobBoardWithTeams($organizationHostedJobsPageName: String!) {"
            "  jobBoard: jobBoardWithTeams("
            "    organizationHostedJobsPageName: $organizationHostedJobsPageName"
            "  ) {"
            "    teams { name jobs { id title locationName employmentType } }"
            "  }"
            "}"
        ),
    }
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=15)
            if resp.status_code != 200:
                logger.warning(f"Ashby returned {resp.status_code} for {company_slug}")
                return jobs

            data = resp.json()
            board = data.get("data", {}).get("jobBoard", {})
            company_name = company_slug.replace("-", " ").title()
            for team in board.get("teams", []):
                for j in team.get("jobs", []):
                    job_id = j.get("id", "")
                    jobs.append(ScrapedJob(
                        title=j.get("title", ""),
                        company=company_name,
                        location=j.get("locationName", ""),
                        application_link=f"https://jobs.ashbyhq.com/{company_slug}/{job_id}",
                        source="ashby",
                    ))
    except Exception as e:
        logger.error(f"Error scraping Ashby for {company_slug}: {e}")
    return jobs


# ── SmartRecruiters scraper (JSON API) ───────────────────────

async def scrape_smartrecruiters(company_slug: str) -> List[ScrapedJob]:
    """
    Scrape jobs from SmartRecruiters.
    URL: https://jobs.smartrecruiters.com/{company_slug}
    Uses their public API.
    """
    jobs = []
    url = f"https://api.smartrecruiters.com/v1/companies/{company_slug}/postings"
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=15)
            if resp.status_code != 200:
                logger.warning(f"SmartRecruiters returned {resp.status_code} for {company_slug}")
                return jobs

            data = resp.json()
            company_name = company_slug.replace("-", " ").title()
            for item in data.get("content", []):
                loc = item.get("location", {})
                loc_parts = [loc.get("city", ""), loc.get("region", ""), loc.get("country", "")]
                loc_str = ", ".join(p for p in loc_parts if p)

                jobs.append(ScrapedJob(
                    title=item.get("name", ""),
                    company=item.get("company", {}).get("name", company_name),
                    description=item.get("customField", [{}])[0].get("valueLabel", "") if item.get("customField") else "",
                    location=loc_str,
                    application_link=f"https://jobs.smartrecruiters.com/{company_slug}/{item.get('id', '')}",
                    source="smartrecruiters",
                ))
    except Exception as e:
        logger.error(f"Error scraping SmartRecruiters for {company_slug}: {e}")
    return jobs


# ── BambooHR scraper (JSON API) ──────────────────────────────

async def scrape_bamboohr(company_slug: str) -> List[ScrapedJob]:
    """
    Scrape jobs from BambooHR job boards.
    URL: https://{company_slug}.bamboohr.com/careers
    """
    jobs = []
    url = f"https://{company_slug}.bamboohr.com/careers/list"
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                url,
                headers={**_BROWSER_HEADERS, "Accept": "application/json"},
                timeout=15,
            )
            if resp.status_code != 200:
                logger.warning(f"BambooHR returned {resp.status_code} for {company_slug}")
                return jobs

            data = resp.json()
            company_name = company_slug.replace("-", " ").title()
            for item in data.get("result", []):
                loc = item.get("location", {})
                loc_str = loc.get("city", "")
                if loc.get("state"):
                    loc_str += f", {loc['state']}"

                jobs.append(ScrapedJob(
                    title=item.get("jobOpeningName", ""),
                    company=company_name,
                    location=loc_str,
                    application_link=f"https://{company_slug}.bamboohr.com/careers/{item.get('id', '')}",
                    source="bamboohr",
                ))
    except Exception as e:
        logger.error(f"Error scraping BambooHR for {company_slug}: {e}")
    return jobs


# ── Workable scraper (JSON API) ──────────────────────────────

async def scrape_workable(company_slug: str) -> List[ScrapedJob]:
    """
    Scrape jobs from Workable ATS.
    URL: https://apply.workable.com/{company_slug}
    """
    jobs = []
    url = f"https://apply.workable.com/api/v3/accounts/{company_slug}/jobs"
    payload = {"query": "", "location": [], "department": [], "worktype": [], "remote": []}
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=15)
            if resp.status_code != 200:
                logger.warning(f"Workable returned {resp.status_code} for {company_slug}")
                return jobs

            data = resp.json()
            company_name = company_slug.replace("-", " ").title()
            for item in data.get("results", []):
                loc_parts = []
                if item.get("city"):
                    loc_parts.append(item["city"])
                if item.get("country"):
                    loc_parts.append(item["country"])
                if item.get("remote"):
                    loc_parts.append("Remote")

                jobs.append(ScrapedJob(
                    title=item.get("title", ""),
                    company=company_name,
                    location=", ".join(loc_parts),
                    application_link=f"https://apply.workable.com/{company_slug}/j/{item.get('shortcode', '')}/",
                    source="workable",
                ))
    except Exception as e:
        logger.error(f"Error scraping Workable for {company_slug}: {e}")
    return jobs


# ── JazzHR scraper (JSON API) ────────────────────────────────

async def scrape_jazzhr(company_slug: str) -> List[ScrapedJob]:
    """
    Scrape jobs from JazzHR boards.
    URL: https://{company_slug}.applytojob.com/apply
    """
    jobs = []
    url = f"https://{company_slug}.applytojob.com/api/jobs"
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=_BROWSER_HEADERS, timeout=15)
            if resp.status_code != 200:
                # Fallback: try /apply endpoint
                resp = await client.get(
                    f"https://{company_slug}.applytojob.com/apply",
                    headers=_BROWSER_HEADERS,
                    timeout=15,
                )
                if resp.status_code != 200:
                    return jobs

                # Parse HTML for job links
                text = resp.text
                titles = re.findall(r'class="job-title[^"]*"[^>]*>([^<]+)', text)
                links = re.findall(r'href="(/apply/[^"]+)"', text)
                company_name = company_slug.replace("-", " ").title()
                for t, link in zip(titles, links):
                    jobs.append(ScrapedJob(
                        title=t.strip(),
                        company=company_name,
                        application_link=f"https://{company_slug}.applytojob.com{link}",
                        source="jazzhr",
                    ))
                return jobs

            data = resp.json()
            company_name = company_slug.replace("-", " ").title()
            for item in data if isinstance(data, list) else data.get("jobs", []):
                jobs.append(ScrapedJob(
                    title=item.get("title", ""),
                    company=company_name,
                    location=item.get("city", ""),
                    application_link=item.get("url", ""),
                    source="jazzhr",
                ))
    except Exception as e:
        logger.error(f"Error scraping JazzHR for {company_slug}: {e}")
    return jobs


# ── Workday scraper (Playwright-based rendering) ─────────────

async def scrape_workday(company_slug: str, company_name: str = "") -> List[ScrapedJob]:
    """
    Scrape jobs from Workday career sites.
    URL format: https://{company_slug}.wd5.myworkdayjobs.com/en-US/External
    Workday uses heavy JS rendering so Playwright is needed.
    """
    jobs = []
    browser = None
    display_name = company_name or company_slug.replace("-", " ").title()

    # Workday tenants use various sub-domains; try a common pattern
    urls_to_try = [
        f"https://{company_slug}.wd5.myworkdayjobs.com/en-US/External",
        f"https://{company_slug}.wd1.myworkdayjobs.com/en-US/External",
        f"https://{company_slug}.wd3.myworkdayjobs.com/en-US/External",
    ]

    try:
        from playwright.async_api import async_playwright, TimeoutError as PWTimeout

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            ctx = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=_BROWSER_HEADERS["User-Agent"],
            )
            page = await ctx.new_page()

            loaded = False
            for workday_url in urls_to_try:
                try:
                    resp = await page.goto(workday_url, wait_until="domcontentloaded", timeout=20000)
                    if resp and resp.status < 400:
                        loaded = True
                        break
                except PWTimeout:
                    continue

            if not loaded:
                logger.warning(f"Workday: could not load any URL for {company_slug}")
                await browser.close()
                return jobs

            await page.wait_for_timeout(4000)

            cards = await page.query_selector_all(
                "li[class*='css-'] a[data-automation-id='jobTitle'], a[data-automation-id='jobTitle']"
            )
            seen = set()
            for el in cards[:50]:
                try:
                    title = (await el.inner_text()).strip()
                    href = await el.get_attribute("href") or ""

                    if not title or href in seen:
                        continue
                    seen.add(href)

                    if href and not href.startswith("http"):
                        href = urljoin(page.url, href)

                    # Try to find location from sibling
                    location = ""
                    try:
                        loc_el = await el.evaluate_handle(
                            "el => el.closest('li')?.querySelector('[data-automation-id=\"locations\"]')"
                        )
                        if loc_el:
                            location = await loc_el.evaluate("el => el.textContent || ''")
                    except Exception:
                        pass

                    jobs.append(ScrapedJob(
                        title=title,
                        company=display_name,
                        location=location.strip(),
                        application_link=href,
                        source="workday",
                    ))
                except Exception:
                    continue

            await ctx.close()
            await browser.close()
            logger.info(f"Workday: scraped {len(jobs)} jobs for {company_slug}")
    except Exception as e:
        logger.error(f"Error scraping Workday for {company_slug}: {e}")
        if browser:
            try:
                await browser.close()
            except Exception:
                pass
    return jobs


# ── Generic Playwright scraper ───────────────────────────────

async def scrape_career_page(url: str, company_name: str) -> List[ScrapedJob]:
    """
    Generic career page scraper using Playwright.
    Attempts to find job listings from any career page structure.
    Enhanced with better selectors, error handling, and content extraction.
    """
    jobs = []
    browser = None

    try:
        from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = await context.new_page()

            # Navigate with better timeout handling
            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
            except PlaywrightTimeoutError:
                logger.warning(f"Network idle timeout for {url}, using domcontentloaded")
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # Wait for potential dynamic content
            await page.wait_for_timeout(2000)

            # Enhanced selectors with priority order
            selectors = [
                # Greenhouse/Lever specific
                ".opening a[href*='job']",
                ".job-post a",
                "div[data-qa='job-board-list'] a",

                # Generic job listing patterns
                "a[href*='job']",
                "a[href*='position']",
                "a[href*='career']",
                "a[href*='opening']",

                # Common class names
                ".job-listing a",
                ".careers-list a",
                ".job-item a",
                ".position-item a",
                "[data-job] a",
                ".job a",

                # Role-based selectors
                "[role='listitem'] a",
                "li a[href*='apply']",
            ]

            seen_links = set()

            for selector in selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        logger.info(f"Found {len(elements)} elements with selector: {selector}")

                        for el in elements[:50]:  # Increased limit
                            try:
                                title = (await el.inner_text()).strip()
                                href = await el.get_attribute("href") or ""

                                # Skip invalid or duplicate entries
                                if not title or len(title) < 3 or len(title) > 200:
                                    continue

                                # Normalize URL
                                if href:
                                    if not href.startswith("http"):
                                        from urllib.parse import urljoin
                                        href = urljoin(url, href)

                                    # Skip duplicates
                                    if href in seen_links:
                                        continue
                                    seen_links.add(href)

                                    # Try to extract location and description from parent
                                    location = ""
                                    description = ""

                                    try:
                                        parent = await el.evaluate_handle("element => element.parentElement")
                                        parent_text = await parent.evaluate("el => el.textContent")

                                        # Basic location detection
                                        location_patterns = [
                                            r"(Remote|Hybrid|On-site)",
                                            r"([A-Z][a-z]+,\s*[A-Z]{2})",
                                            r"([A-Z][a-z]+\s*\|\s*[A-Z][a-z]+)"
                                        ]
                                        for pattern in location_patterns:
                                            match = re.search(pattern, parent_text or "")
                                            if match:
                                                location = match.group(1)
                                                break
                                    except Exception:
                                        pass

                                    jobs.append(ScrapedJob(
                                        title=title,
                                        company=company_name,
                                        application_link=href,
                                        location=location,
                                        description=description,
                                        source="career_page",
                                    ))
                            except Exception as elem_error:
                                logger.debug(f"Error processing element: {elem_error}")
                                continue

                        if jobs:
                            break  # Use first matching selector that found jobs

                except Exception as selector_error:
                    logger.debug(f"Error with selector {selector}: {selector_error}")
                    continue

            await context.close()
            await browser.close()

            logger.info(f"Scraped {len(jobs)} unique jobs from {url}")

    except Exception as e:
        logger.error(f"Error scraping career page {url}: {e}", exc_info=True)
        if browser:
            try:
                await browser.close()
            except:
                pass

    return jobs


# ── Utility ──────────────────────────────────────────────────

def _strip_html(html: str) -> str:
    """Remove HTML tags from a string."""
    return re.sub(r"<[^>]+>", " ", html).strip()


# ── Database Integration ─────────────────────────────────────

async def save_jobs_to_db(scraped_jobs: List[ScrapedJob], db: AsyncSession) -> Dict[str, Any]:
    """
    Save scraped jobs to database with deduplication.
    Returns stats about saved/updated/skipped jobs.
    """
    from ..models import Job

    stats = {
        "total_scraped": len(scraped_jobs),
        "new_jobs": 0,
        "updated_jobs": 0,
        "skipped_jobs": 0,
        "errors": 0
    }

    for scraped_job in scraped_jobs:
        try:
            # Check if job already exists (by title + company + application_link)
            existing_job_query = select(Job).where(
                Job.title == scraped_job.title,
                Job.company == scraped_job.company,
            )

            # Also check by application link if available
            if scraped_job.application_link:
                existing_job_query = existing_job_query.where(
                    Job.application_link == scraped_job.application_link
                )

            result = await db.execute(existing_job_query)
            existing_job = result.scalar_one_or_none()

            if existing_job:
                # Update if description or location changed
                updated = False
                if scraped_job.description and scraped_job.description != existing_job.description:
                    existing_job.description = scraped_job.description
                    updated = True
                if scraped_job.location and scraped_job.location != existing_job.location:
                    existing_job.location = scraped_job.location
                    updated = True

                if updated:
                    stats["updated_jobs"] += 1
                else:
                    stats["skipped_jobs"] += 1
            else:
                # Create new job
                new_job = Job(
                    title=scraped_job.title,
                    company=scraped_job.company,
                    description=scraped_job.description or "No description available",
                    location=scraped_job.location or "Not specified",
                    application_link=scraped_job.application_link,
                    source=scraped_job.source,
                    posting_date=scraped_job.posting_date,
                )
                db.add(new_job)
                stats["new_jobs"] += 1

        except Exception as e:
            logger.error(f"Error saving job {scraped_job.title}: {e}")
            stats["errors"] += 1
            await db.rollback()
            continue

    # Batch commit all changes at once
    try:
        await db.commit()
    except Exception as e:
        logger.error(f"Error committing batch: {e}")
        await db.rollback()

    logger.info(f"DB Save Stats: {stats}")
    return stats


async def scrape_and_save(
    scraper_type: str,
    identifier: str,
    db: AsyncSession,
    custom_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Unified function to scrape and save jobs to database.

    Args:
        scraper_type: One of 'greenhouse', 'lever', 'career_page'
        identifier: Company slug (for greenhouse/lever) or company name (for career_page)
        db: Database session
        custom_url: Required for career_page type

    Returns:
        Dictionary with scraping and saving stats
    """
    jobs = []

    try:
        if scraper_type == "greenhouse":
            jobs = await scrape_greenhouse(identifier)
        elif scraper_type == "lever":
            jobs = await scrape_lever(identifier)
        elif scraper_type == "linkedin":
            jobs = await scrape_linkedin(identifier, custom_url or "")
        elif scraper_type == "naukri":
            jobs = await scrape_naukri(identifier, custom_url or "")
        elif scraper_type == "indeed":
            jobs = await scrape_indeed(identifier, custom_url or "")
        elif scraper_type == "glassdoor":
            jobs = await scrape_glassdoor(identifier, custom_url or "")
        elif scraper_type == "remoteok":
            jobs = await scrape_remoteok(identifier)
        elif scraper_type == "arbeitnow":
            jobs = await scrape_arbeitnow(identifier)
        elif scraper_type == "ashby":
            jobs = await scrape_ashby(identifier)
        elif scraper_type == "smartrecruiters":
            jobs = await scrape_smartrecruiters(identifier)
        elif scraper_type == "bamboohr":
            jobs = await scrape_bamboohr(identifier)
        elif scraper_type == "workable":
            jobs = await scrape_workable(identifier)
        elif scraper_type == "jazzhr":
            jobs = await scrape_jazzhr(identifier)
        elif scraper_type == "workday":
            jobs = await scrape_workday(identifier, custom_url or "")
        elif scraper_type == "career_page":
            if not custom_url:
                raise ValueError("custom_url is required for career_page scraper")
            jobs = await scrape_career_page(custom_url, identifier)
        else:
            raise ValueError(f"Unknown scraper_type: {scraper_type}")

        if not jobs:
            return {
                "success": True,
                "message": f"No jobs found for {identifier}",
                "scraper_type": scraper_type,
                "jobs_found": 0
            }

        # Save to database
        save_stats = await save_jobs_to_db(jobs, db)

        return {
            "success": True,
            "message": f"Successfully scraped {identifier}",
            "scraper_type": scraper_type,
            "jobs_found": len(jobs),
            **save_stats
        }

    except Exception as e:
        logger.error(f"Error in scrape_and_save for {identifier}: {e}")
        return {
            "success": False,
            "message": str(e),
            "scraper_type": scraper_type,
            "jobs_found": 0,
            "error": str(e)
        }
