"""
Preferences router — get and update user job preferences.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User, Preference
from ..schemas import PreferenceRequest, PreferenceResponse
from ..auth import get_current_user

router = APIRouter()


@router.get("/", response_model=PreferenceResponse)
async def get_preferences(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the current user's job preferences."""
    result = await db.execute(select(Preference).where(Preference.user_id == user.id))
    prefs = result.scalar_one_or_none()
    if not prefs:
        # Auto-create default preferences
        prefs = Preference(user_id=user.id)
        db.add(prefs)
        await db.flush()
        await db.refresh(prefs)
    return prefs


@router.put("/", response_model=PreferenceResponse)
async def update_preferences(
    body: PreferenceRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the current user's job preferences."""
    result = await db.execute(select(Preference).where(Preference.user_id == user.id))
    prefs = result.scalar_one_or_none()
    if not prefs:
        prefs = Preference(user_id=user.id)
        db.add(prefs)

    # Update fields
    prefs.role_titles = body.role_titles
    prefs.locations = body.locations
    prefs.salary_min = body.salary_min
    prefs.salary_max = body.salary_max
    prefs.experience_level = body.experience_level
    prefs.remote_preference = body.remote_preference
    prefs.priority_companies = body.priority_companies

    await db.flush()
    await db.refresh(prefs)
    return prefs
