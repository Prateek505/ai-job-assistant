"""
Pydantic request / response schemas.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# ── Auth ────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=5)
    password: str = Field(..., min_length=6)
    name: str = Field(..., min_length=1)


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Resume ──────────────────────────────────────────────────

class ResumeResponse(BaseModel):
    id: int
    filename: str
    raw_text: str
    parsed_json: dict
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Preferences ─────────────────────────────────────────────

class PreferenceRequest(BaseModel):
    role_titles: List[str] = []
    locations: List[str] = []
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    experience_level: Optional[str] = None
    remote_preference: Optional[str] = "any"
    priority_companies: List[str] = []


class PreferenceResponse(PreferenceRequest):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)


# ── Job ─────────────────────────────────────────────────────

class JobResponse(BaseModel):
    id: int
    title: str
    company: str
    description: str
    location: Optional[str]
    salary_range: Optional[str]
    posting_date: Optional[datetime]
    deadline: Optional[datetime]
    application_link: Optional[str]
    source: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobCreate(BaseModel):
    title: str
    company: str
    description: str = ""
    location: Optional[str] = None
    salary_range: Optional[str] = None
    posting_date: Optional[datetime] = None
    deadline: Optional[datetime] = None
    application_link: Optional[str] = None
    source: Optional[str] = None


# ── Job Match ───────────────────────────────────────────────

class JobMatchResponse(BaseModel):
    id: int
    job_id: int
    score: float
    skill_similarity: float
    experience_match: float
    location_preference: float
    salary_preference: float
    company_priority: float
    status: str
    created_at: datetime
    job: Optional[JobResponse] = None

    model_config = ConfigDict(from_attributes=True)


class MatchStatusUpdate(BaseModel):
    status: str  # new, saved, applied, rejected


# ── Notification ────────────────────────────────────────────

class NotificationResponse(BaseModel):
    id: int
    type: str
    title: str
    message: str
    read: bool
    job_id: Optional[int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Resume Optimization ────────────────────────────────────

class ResumeOptimizationResponse(BaseModel):
    missing_keywords: List[str]
    missing_skills: List[str]
    suggestions: List[str]
    optimized_text: str


# ── Cover Letter ────────────────────────────────────────────

class CoverLetterResponse(BaseModel):
    cover_letter: str
    job_title: str
    company: str


# ── Networking ──────────────────────────────────────────────

class NetworkingContact(BaseModel):
    name: str
    role: str
    department: str
    connection_message: str


class NetworkingResponse(BaseModel):
    company: str
    contacts: List[NetworkingContact]
    tips: List[str]
