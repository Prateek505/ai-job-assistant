"""
Jobs router — list/search jobs, get job details, resume optimisation,
cover letter generation, and networking suggestions.
"""

from typing import Optional, List
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User, Job, Resume, Preference
from ..schemas import (
    JobResponse, JobCreate,
    ResumeOptimizationResponse, CoverLetterResponse, NetworkingResponse,
)
from ..auth import get_current_user
from ..services.resume_optimizer import optimize_resume_for_job
from ..services.cover_letter import generate_cover_letter
from ..services.networking import suggest_networking
from ..services.ai_matcher import compute_match_scores

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Location alias map for smart filtering ─────────────────────────────
# When user types a country name, expand to also match its major cities.
# Keys are lowercase. Values are city strings also matched with ILIKE.
_LOCATION_ALIASES: dict[str, list[str]] = {
    "india": [
        "bangalore", "bengaluru", "mumbai", "delhi", "hyderabad",
        "chennai", "pune", "kolkata", "noida", "gurgaon", "gurugram",
        "ahmedabad", "jaipur", "kochi", "thiruvananthapuram", "india", "in",
    ],
    "us": ["united states", "new york", "san francisco", "seattle", "austin",
            "chicago", "boston", "los angeles", "denver"],
    "usa": ["united states", "new york", "san francisco", "seattle", "austin",
             "chicago", "boston", "los angeles", "denver"],
    "uk": ["united kingdom", "london", "manchester", "birmingham", "edinburgh"],
    "germany": ["berlin", "munich", "frankfurt", "hamburg", "cologne"],
    "canada": ["toronto", "vancouver", "montreal", "calgary", "ottawa"],
    "australia": ["sydney", "melbourne", "brisbane", "perth", "canberra"],
}


@router.get("/", response_model=list[JobResponse])
async def list_jobs(
    search: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    company: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    List jobs with optional filters, automatically sorted by relevance to user.
    Jobs are matched against user's resume and preferences.
    """
    # Fetch user's resume and preferences for matching
    resume_result = await db.execute(
        select(Resume).where(Resume.user_id == user.id).order_by(Resume.uploaded_at.desc())
    )
    resume = resume_result.scalars().first()

    pref_result = await db.execute(
        select(Preference).where(Preference.user_id == user.id)
    )
    preferences = pref_result.scalar_one_or_none()

    # Build base query
    query = select(Job)

    if search:
        query = query.where(
            or_(
                Job.title.ilike(f"%{search}%"),
                Job.description.ilike(f"%{search}%"),
                Job.company.ilike(f"%{search}%"),
            )
        )
    if location:
        loc_lower = location.lower().strip()
        # Expand country names to city aliases for smart filtering
        aliases = _LOCATION_ALIASES.get(loc_lower, [])
        if aliases:
            # Match any alias OR the literal term
            loc_conditions = [Job.location.ilike(f"%{alias}%") for alias in aliases]
            loc_conditions.append(Job.location.ilike(f"%{location}%"))
            query = query.where(or_(*loc_conditions))
        else:
            query = query.where(Job.location.ilike(f"%{location}%"))
    if company:
        query = query.where(Job.company.ilike(f"%{company}%"))

    # Get all matching jobs
    result = await db.execute(query)
    all_jobs = result.scalars().all()

    # If user has a resume, compute match scores and sort by relevance
    if resume and all_jobs:
        jobs_with_scores = []
        for job in all_jobs:
            try:
                scores = compute_match_scores(resume, job, preferences)
                jobs_with_scores.append((job, scores["total"]))
            except Exception as e:
                logger.warning(f"Error computing match score for job {job.id}: {e}")
                jobs_with_scores.append((job, 50.0))  # Default score on error

        # Sort by match score (highest first)
        jobs_with_scores.sort(key=lambda x: x[1], reverse=True)
        sorted_jobs = [job for job, _ in jobs_with_scores]
    else:
        # No resume - sort by creation date
        sorted_jobs = sorted(all_jobs, key=lambda j: j.created_at or 0, reverse=True)

    # Apply pagination
    paginated_jobs = sorted_jobs[skip:skip + limit]

    return paginated_jobs


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single job by ID."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/", response_model=JobResponse, status_code=201)
async def create_job(
    body: JobCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually add a job listing (for testing/demo purposes)."""
    job = Job(**body.model_dump())
    db.add(job)
    await db.flush()
    await db.refresh(job)
    return job


@router.get("/{job_id}/optimize-resume", response_model=ResumeOptimizationResponse)
async def optimize_resume(
    job_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get resume optimization suggestions for a specific job."""
    job_result = await db.execute(select(Job).where(Job.id == job_id))
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    resume_result = await db.execute(
        select(Resume).where(Resume.user_id == user.id).order_by(Resume.uploaded_at.desc())
    )
    resume = resume_result.scalars().first()
    if not resume:
        raise HTTPException(status_code=400, detail="Please upload a resume first")

    return await optimize_resume_for_job(resume, job)


@router.get("/{job_id}/cover-letter", response_model=CoverLetterResponse)
async def get_cover_letter(
    job_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a tailored cover letter for a specific job."""
    job_result = await db.execute(select(Job).where(Job.id == job_id))
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    resume_result = await db.execute(
        select(Resume).where(Resume.user_id == user.id).order_by(Resume.uploaded_at.desc())
    )
    resume = resume_result.scalars().first()
    if not resume:
        raise HTTPException(status_code=400, detail="Please upload a resume first")

    return await generate_cover_letter(resume, job)


@router.get("/{job_id}/networking", response_model=NetworkingResponse)
async def get_networking(
    job_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get networking suggestions for the company of a specific job."""
    job_result = await db.execute(select(Job).where(Job.id == job_id))
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return await suggest_networking(job)
