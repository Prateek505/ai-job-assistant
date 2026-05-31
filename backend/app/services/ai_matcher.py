"""
AI Matcher — computes weighted match scores between a resume and a job.

Scoring weights:
  - Skill similarity:      50%
  - Experience match:      20%
  - Location preference:   15%
  - Salary preference:     10%
  - Company priority:       5%
"""

from ..models import Resume, Job, Preference


def compute_match_scores(resume: Resume, job: Job, preferences: Preference | None) -> dict:
    """
    Compute a weighted match score between a resume and a job listing.
    Returns a dict with individual components and the total score (0–100).
    """
    skill_sim = _skill_similarity(resume, job)
    exp_match = _experience_match(resume, job)
    loc_pref = _location_preference(job, preferences)
    sal_pref = _salary_preference(job, preferences)
    comp_prio = _company_priority(job, preferences)

    total = (
        skill_sim * 0.50
        + exp_match * 0.20
        + loc_pref * 0.15
        + sal_pref * 0.10
        + comp_prio * 0.05
    )

    return {
        "skill_similarity": round(skill_sim, 2),
        "experience_match": round(exp_match, 2),
        "location_preference": round(loc_pref, 2),
        "salary_preference": round(sal_pref, 2),
        "company_priority": round(comp_prio, 2),
        "total": round(total, 2),
    }


def _skill_similarity(resume: Resume, job: Job) -> float:
    """
    Compare resume skills against job description keywords.
    Returns 0–100 score based on overlap.
    """
    resume_skills = set()
    parsed = resume.parsed_json or {}
    for key in ("skills", "technologies"):
        for s in parsed.get(key, []):
            resume_skills.add(s.lower().strip())

    if not resume_skills:
        # Fall back to raw text word matching
        resume_words = set(resume.raw_text.lower().split())
        resume_skills = resume_words

    job_text = (job.title + " " + job.description).lower()

    if not resume_skills:
        return 50.0  # Neutral when no data

    matches = sum(1 for skill in resume_skills if skill in job_text)
    ratio = min(matches / max(len(resume_skills) * 0.3, 1), 1.0)
    return ratio * 100


def _experience_match(resume: Resume, job: Job) -> float:
    """
    Heuristic experience match.
    Checks if resume mentions experience-related terms found in the job.
    """
    parsed = resume.parsed_json or {}
    experiences = parsed.get("experience", [])
    job_lower = job.description.lower()

    # Check years of experience keywords
    experience_keywords = ["senior", "junior", "lead", "principal", "intern", "entry", "mid"]
    resume_text = resume.raw_text.lower()

    score = 60.0  # Base score
    for kw in experience_keywords:
        if kw in job_lower and kw in resume_text:
            score += 10.0

    if experiences:
        score += min(len(experiences) * 5, 20)

    return min(score, 100.0)


def _location_preference(job: Job, preferences: Preference | None) -> float:
    """Check if job location matches user preferred locations."""
    if not preferences or not preferences.locations:
        return 80.0  # Neutral

    if not job.location:
        return 60.0

    job_loc = job.location.lower()
    for loc in preferences.locations:
        if loc.lower() in job_loc or job_loc in loc.lower():
            return 100.0

    if "remote" in job_loc:
        if preferences.remote_preference in ("remote", "any"):
            return 90.0

    return 40.0


def _salary_preference(job: Job, preferences: Preference | None) -> float:
    """Check if job salary range overlaps with user preference."""
    if not preferences or not (preferences.salary_min or preferences.salary_max):
        return 80.0

    if not job.salary_range:
        return 60.0

    # Try to extract numbers from salary_range string
    import re
    numbers = re.findall(r"\d+", job.salary_range.replace(",", ""))
    if not numbers:
        return 60.0

    job_salaries = [int(n) for n in numbers if int(n) > 1000]
    if not job_salaries:
        return 60.0

    job_max = max(job_salaries)
    job_min = min(job_salaries)

    # Check overlap
    user_min = preferences.salary_min or 0
    user_max = preferences.salary_max or 999999999

    if job_max >= user_min and job_min <= user_max:
        return 100.0
    elif job_max < user_min:
        gap = (user_min - job_max) / user_min
        return max(100 - gap * 200, 20)

    return 50.0


def _company_priority(job: Job, preferences: Preference | None) -> float:
    """Check if job company is in user's priority list."""
    if not preferences or not preferences.priority_companies:
        return 50.0

    company_lower = job.company.lower()
    for pc in preferences.priority_companies:
        if pc.lower() in company_lower or company_lower in pc.lower():
            return 100.0

    return 30.0
