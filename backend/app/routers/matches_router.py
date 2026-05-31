"""
Matches router — view ranked job matches and refresh scoring.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import User, Job, Resume, JobMatch, Preference
from ..schemas import JobMatchResponse, MatchStatusUpdate
from ..auth import get_current_user
from ..services.ai_matcher import compute_match_scores

router = APIRouter()


@router.get("/", response_model=list[JobMatchResponse])
async def list_matches(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all job matches for the current user, ranked by score."""
    result = await db.execute(
        select(JobMatch)
        .options(selectinload(JobMatch.job))
        .where(JobMatch.user_id == user.id)
        .order_by(JobMatch.score.desc())
    )
    return result.scalars().all()


@router.post("/refresh", status_code=200)
async def refresh_matches(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Re-compute match scores for all jobs against the user's latest resume."""
    # Get latest resume
    resume_result = await db.execute(
        select(Resume).where(Resume.user_id == user.id).order_by(Resume.uploaded_at.desc())
    )
    resume = resume_result.scalars().first()
    if not resume:
        raise HTTPException(status_code=400, detail="Please upload a resume first")

    # Get user preferences
    pref_result = await db.execute(select(Preference).where(Preference.user_id == user.id))
    preferences = pref_result.scalar_one_or_none()

    # Get all jobs
    jobs_result = await db.execute(select(Job))
    jobs = jobs_result.scalars().all()

    if not jobs:
        return {"message": "No jobs to match against", "matches_created": 0}

    # Build map of existing matches to preserve user status (saved/applied/rejected)
    old_matches_result = await db.execute(select(JobMatch).where(JobMatch.user_id == user.id))
    existing_map = {m.job_id: m for m in old_matches_result.scalars().all()}

    # Compute new match scores (upsert: update existing, create new)
    matches_created = 0
    matches_updated = 0
    for job in jobs:
        scores = compute_match_scores(resume, job, preferences)

        if job.id in existing_map:
            # Update scores but preserve user-set status
            m = existing_map[job.id]
            m.score = scores["total"]
            m.skill_similarity = scores["skill_similarity"]
            m.experience_match = scores["experience_match"]
            m.location_preference = scores["location_preference"]
            m.salary_preference = scores["salary_preference"]
            m.company_priority = scores["company_priority"]
            matches_updated += 1
        else:
            match = JobMatch(
                user_id=user.id,
                job_id=job.id,
                score=scores["total"],
                skill_similarity=scores["skill_similarity"],
                experience_match=scores["experience_match"],
                location_preference=scores["location_preference"],
                salary_preference=scores["salary_preference"],
                company_priority=scores["company_priority"],
            )
            db.add(match)
            matches_created += 1

    await db.flush()
    return {"message": "Matches refreshed", "matches_created": matches_created, "matches_updated": matches_updated}


@router.put("/{match_id}/status", response_model=JobMatchResponse)
async def update_match_status(
    match_id: int,
    body: MatchStatusUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the application status of a job match."""
    result = await db.execute(
        select(JobMatch)
        .options(selectinload(JobMatch.job))
        .where(JobMatch.id == match_id, JobMatch.user_id == user.id)
    )
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    match.status = body.status
    await db.flush()
    await db.refresh(match)
    return match
