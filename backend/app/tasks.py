"""
Celery task definitions for background processing.
Tasks: scan_jobs, match_jobs_for_user, send_deadline_alerts.

NOTE: Requires Redis to be running. Start worker with:
  celery -A app.tasks worker -l info
"""

import logging
from celery import Celery
from .config import settings

logger = logging.getLogger(__name__)

celery_app = Celery(
    "jobai",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "scan-jobs-frequently": {
            "task": "app.tasks.scan_jobs",
            "schedule": 300.0,  # Every 5 minutes for prototype
        },
        "deadline-alerts-daily": {
            "task": "app.tasks.send_deadline_alerts",
            "schedule": 86400.0,  # Daily
        },
    },
)


@celery_app.task(name="app.tasks.scan_jobs")
def scan_jobs():
    """
    Periodically scan configured career pages for new job listings.
    This task runs asynchronously via Celery Beat.
    Saves scraped jobs to database with deduplication.
    """
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from .config import settings

    async def _scan():
        from .services.job_scraper import scrape_and_save

        # Create async engine and session for background task
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        async_session = async_sessionmaker(engine, expire_on_commit=False)

        # ── ATS Company Boards (slug-based scrapers) ──────────

        # Greenhouse companies (most tech companies use Greenhouse)
        greenhouse_companies = [
            # Big Tech & FAANG
            "google", "meta", "amazon", "apple", "microsoft",
            # AI/ML Companies
            "openai", "anthropic", "deepmind", "cohere", "huggingface",
            "stability", "midjourney", "replicate", "scale", "weights-and-biases",
            # Unicorns & High-Growth Startups
            "figma", "notion", "vercel", "stripe", "databricks",
            "airtable", "linear", "retool", "webflow", "framer",
            "loom", "miro", "coda", "pitch", "superhuman",
            # Fintech
            "plaid", "brex", "ramp", "mercury", "coinbase",
            "blockchain", "kraken", "gemini", "anchorage", "paxos",
            # Developer Tools
            "github", "gitlab", "hashicorp", "datadog", "snyk",
            "launchdarkly", "postman", "insomnia", "nx", "turbo",
            # Cloud & Infrastructure
            "cloudflare", "fastly", "render", "railway", "fly",
            "planetscale", "supabase", "neon", "cockroachlabs", "timescale",
            # E-commerce & Marketplace
            "shopify", "faire", "instacart", "doordash", "grubhub",
            "airbnb", "vrbo", "turo", "getaround", "outdoorsy",
            # Health Tech
            "tempus", "flatiron", "veracyte", "guardanthealth", "grail",
            "ro", "hims", "nurx", "alto", "capsule",
            # Enterprise SaaS
            "salesforce", "hubspot", "zendesk", "intercom", "drift",
            "gong", "outreach", "salesloft", "clearbit", "zoominfo",
            # Security
            "crowdstrike", "sentinelone", "lacework", "orca-security", "wiz",
            # Gaming & Entertainment
            "roblox", "epicgames", "unity", "discord", "twitch",
            # Hardware & Robotics
            "tesla", "rivian", "lucid", "cruise", "waymo",
            "anduril", "palantir", "relativity", "spaceexploration",
        ]

        # Lever companies
        lever_companies = [
            "netflix", "canva", "robinhood", "chime", "sofi",
            "affirm", "klarna", "afterpay", "marqeta", "checkout",
            "twilio", "sendgrid", "messagebird", "vonage", "bandwidth",
            "okta", "auth0", "onelogin", "ping", "forgerock",
            "elastic", "mongodb", "redis", "confluent", "cockroach",
            "segment", "amplitude", "mixpanel", "heap", "fullstory",
            "figma", "invision", "sketch", "abstract", "zeplin",
            "asana", "monday", "clickup", "wrike", "teamwork",
            "dropbox", "box", "egnyte", "sharefile", "citrix",
        ]

        # Ashby ATS companies
        ashby_companies = [
            "ramp", "notion", "linear", "vercel", "anthropic",
            "retool", "loom", "dbt-labs", "anyscale", "replit",
        ]

        # SmartRecruiters companies
        smartrecruiters_companies = [
            "Visa", "Bosch", "McDonald", "IKEA", "Skechers",
            "LinkedIn", "Equinix", "FireEye", "DocuSign",
        ]

        # Workable companies
        workable_companies = [
            "posthog", "cal-com", "langchain", "grafana",
            "terraform-industries", "vanta", "deel",
        ]

        # BambooHR companies
        bamboohr_companies = [
            "samsara", "lattice", "qualtrics",
        ]

        # ── Job Board searches (keyword-based) ──────────────
        # These search major job portals for common tech roles
        job_board_searches = [
            ("linkedin", "software engineer", ""),
            ("linkedin", "data scientist", ""),
            ("linkedin", "product manager", ""),
            ("linkedin", "machine learning engineer", ""),
            ("naukri", "software developer", ""),
            ("naukri", "data analyst", ""),
            ("naukri", "python developer", ""),
            ("indeed", "software engineer", ""),
            ("indeed", "backend developer", ""),
            ("indeed", "frontend developer", ""),
            ("glassdoor", "software engineer", ""),
            ("remoteok", "react", ""),
            ("remoteok", "python", ""),
            ("remoteok", "devops", ""),
            ("arbeitnow", "software", ""),
            ("arbeitnow", "data", ""),
        ]

        total_stats = {
            "total_scraped": 0,
            "new_jobs": 0,
            "updated_jobs": 0,
            "skipped_jobs": 0,
            "errors": 0
        }

        async def _scrape_one(db, scraper_type, slug, custom_url=None):
            """Scrape a single source and accumulate stats."""
            try:
                result = await scrape_and_save(scraper_type, slug, db, custom_url)
                if result.get("success"):
                    total_stats["total_scraped"] += result.get("jobs_found", 0)
                    total_stats["new_jobs"] += result.get("new_jobs", 0)
                    total_stats["updated_jobs"] += result.get("updated_jobs", 0)
                    total_stats["skipped_jobs"] += result.get("skipped_jobs", 0)
                    logger.info(f"{scraper_type} {slug}: {result.get('jobs_found', 0)} jobs")
                else:
                    total_stats["errors"] += 1
            except Exception as e:
                logger.error(f"Error {scraper_type} {slug}: {e}")
                total_stats["errors"] += 1

        async with async_session() as db:
            # Greenhouse
            for slug in greenhouse_companies:
                await _scrape_one(db, "greenhouse", slug)

            # Lever
            for slug in lever_companies:
                await _scrape_one(db, "lever", slug)

            # Ashby
            for slug in ashby_companies:
                await _scrape_one(db, "ashby", slug)

            # SmartRecruiters
            for slug in smartrecruiters_companies:
                await _scrape_one(db, "smartrecruiters", slug)

            # Workable
            for slug in workable_companies:
                await _scrape_one(db, "workable", slug)

            # BambooHR
            for slug in bamboohr_companies:
                await _scrape_one(db, "bamboohr", slug)

            # Job board searches (LinkedIn, Naukri, Indeed, Glassdoor, RemoteOK, Arbeitnow)
            for scraper_type, keywords, location in job_board_searches:
                await _scrape_one(db, scraper_type, keywords, location or None)

        await engine.dispose()

        logger.info(f"Scan complete! Stats: {total_stats}")
        return total_stats

    try:
        return asyncio.run(_scan())
    except Exception as e:
        logger.error(f"Job scanning error: {e}", exc_info=True)
        return {"error": str(e), "status": "failed"}


@celery_app.task(name="app.tasks.match_jobs_for_user")
def match_jobs_for_user(user_id: int):
    """Re-compute match scores for a specific user."""
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy import select
    from .config import settings

    logger.info(f"Matching jobs for user {user_id}")

    async def _match():
        from .models import User, Job, Resume, Preference, JobMatch
        from .services.ai_matcher import compute_match_scores

        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        async with session_factory() as db:
            # Fetch user's latest resume
            resume_result = await db.execute(
                select(Resume).where(Resume.user_id == user_id).order_by(Resume.uploaded_at.desc())
            )
            resume = resume_result.scalars().first()
            if not resume:
                logger.warning(f"No resume found for user {user_id}, skipping match")
                return {"user_id": user_id, "status": "skipped", "reason": "no_resume"}

            # Fetch preferences
            pref_result = await db.execute(select(Preference).where(Preference.user_id == user_id))
            preferences = pref_result.scalar_one_or_none()

            # Fetch all jobs
            jobs_result = await db.execute(select(Job))
            jobs = jobs_result.scalars().all()

            if not jobs:
                logger.info(f"No jobs in database for user {user_id}")
                return {"user_id": user_id, "status": "completed", "matches": 0}

            # Build set of existing match job_ids with their statuses
            existing_result = await db.execute(
                select(JobMatch).where(JobMatch.user_id == user_id)
            )
            existing_map = {m.job_id: m for m in existing_result.scalars().all()}

            matches_created = 0
            matches_updated = 0
            for job in jobs:
                try:
                    scores = compute_match_scores(resume, job, preferences)
                except Exception as e:
                    logger.error(f"Error computing match for job {job.id}: {e}")
                    continue

                if job.id in existing_map:
                    m = existing_map[job.id]
                    m.score = scores["total"]
                    m.skill_similarity = scores["skill_similarity"]
                    m.experience_match = scores["experience_match"]
                    m.location_preference = scores["location_preference"]
                    m.salary_preference = scores["salary_preference"]
                    m.company_priority = scores["company_priority"]
                    matches_updated += 1
                else:
                    db.add(JobMatch(
                        user_id=user_id,
                        job_id=job.id,
                        score=scores["total"],
                        skill_similarity=scores["skill_similarity"],
                        experience_match=scores["experience_match"],
                        location_preference=scores["location_preference"],
                        salary_preference=scores["salary_preference"],
                        company_priority=scores["company_priority"],
                    ))
                    matches_created += 1

            await db.commit()

        await engine.dispose()
        logger.info(f"User {user_id}: {matches_created} created, {matches_updated} updated")
        return {"user_id": user_id, "status": "completed", "created": matches_created, "updated": matches_updated}

    try:
        return asyncio.run(_match())
    except Exception as e:
        logger.error(f"Match task error for user {user_id}: {e}", exc_info=True)
        return {"user_id": user_id, "status": "failed", "error": str(e)}


@celery_app.task(name="app.tasks.send_deadline_alerts")
def send_deadline_alerts():
    """Check for approaching deadlines and send alerts."""
    import asyncio
    from datetime import datetime, timedelta, timezone
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy import select, and_
    from .config import settings

    logger.info("Checking for approaching deadlines...")

    async def _check_deadlines():
        from .models import User, Job, JobMatch, Notification
        from .services.notifier import send_email_notification

        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        now = datetime.now(timezone.utc)
        deadline_threshold = now + timedelta(days=3)
        alerts_sent = 0

        async with session_factory() as db:
            # Find jobs with deadlines within the next 3 days
            jobs_result = await db.execute(
                select(Job).where(
                    and_(
                        Job.deadline.isnot(None),
                        Job.deadline > now,
                        Job.deadline <= deadline_threshold,
                    )
                )
            )
            upcoming_jobs = jobs_result.scalars().all()

            if not upcoming_jobs:
                logger.info("No upcoming deadlines found")
                await engine.dispose()
                return {"status": "completed", "alerts_sent": 0}

            job_ids = [j.id for j in upcoming_jobs]

            # Find all users who have matches for these jobs
            matches_result = await db.execute(
                select(JobMatch).where(
                    JobMatch.job_id.in_(job_ids),
                    JobMatch.status.in_(["new", "saved"]),
                )
            )
            matches = matches_result.scalars().all()

            # Group matches by user
            user_jobs: dict = {}
            for match in matches:
                user_jobs.setdefault(match.user_id, []).append(match.job_id)

            # Send notifications per user
            for uid, job_id_list in user_jobs.items():
                user_result = await db.execute(select(User).where(User.id == uid))
                user = user_result.scalar_one_or_none()
                if not user:
                    continue

                for jid in job_id_list:
                    job = next((j for j in upcoming_jobs if j.id == jid), None)
                    if not job:
                        continue

                    days_left = (job.deadline - now).days

                    # Create in-app notification
                    notif = Notification(
                        user_id=uid,
                        type="deadline",
                        title=f"Deadline approaching: {job.title}",
                        message=f"{job.company} — {job.title} deadline in {days_left} day(s).",
                        job_id=jid,
                    )
                    db.add(notif)

                    # Send email
                    await send_email_notification(
                        to_email=user.email,
                        subject=f"Deadline Alert: {job.title} at {job.company}",
                        body=f"The application deadline for <b>{job.title}</b> at <b>{job.company}</b> is in {days_left} day(s). Don't miss it!",
                    )
                    alerts_sent += 1

            await db.commit()

        await engine.dispose()
        logger.info(f"Sent {alerts_sent} deadline alerts")
        return {"status": "completed", "alerts_sent": alerts_sent}

    try:
        return asyncio.run(_check_deadlines())
    except Exception as e:
        logger.error(f"Deadline alerts error: {e}", exc_info=True)
        return {"status": "failed", "error": str(e), "alerts_sent": 0}
