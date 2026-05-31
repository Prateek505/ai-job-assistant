"""
Tests for the AI matching score computation.
These are unit tests for the service layer — no HTTP or DB needed.
"""

import pytest
from unittest.mock import MagicMock
from app.services.ai_matcher import compute_match_scores


def _make_resume(skills=None, raw_text=""):
    """Create a mock resume object."""
    mock = MagicMock()
    mock.parsed_json = {"skills": skills or [], "technologies": skills or []}
    mock.raw_text = raw_text
    return mock


def _make_job(title="", description="", company="", location="", salary_range=""):
    """Create a mock job object."""
    mock = MagicMock()
    mock.title = title
    mock.description = description
    mock.company = company
    mock.location = location
    mock.salary_range = salary_range
    return mock


def _make_prefs(locations=None, salary_min=None, salary_max=None, priority_companies=None,
                remote_preference="any"):
    """Create a mock preferences object."""
    mock = MagicMock()
    mock.locations = locations or []
    mock.salary_min = salary_min
    mock.salary_max = salary_max
    mock.priority_companies = priority_companies or []
    mock.remote_preference = remote_preference
    return mock


class TestMatchScoring:
    """Test suite for the weighted match scoring system."""

    def test_perfect_skill_match(self):
        """Resume with all job skills should score high on skill similarity."""
        resume = _make_resume(skills=["python", "fastapi", "docker"])
        job = _make_job(
            title="Python Developer",
            description="We need python, fastapi, and docker experience.",
        )
        scores = compute_match_scores(resume, job, None)
        assert scores["skill_similarity"] > 80

    def test_no_skill_match(self):
        """Resume with no matching skills should score low."""
        resume = _make_resume(skills=["java", "spring"])
        job = _make_job(
            title="Python Developer",
            description="We need python, fastapi, and docker experience.",
        )
        scores = compute_match_scores(resume, job, None)
        assert scores["skill_similarity"] < 50

    def test_location_match(self):
        """Job in preferred location should get high location score."""
        resume = _make_resume(skills=["python"])
        job = _make_job(title="Dev", description="dev", location="San Francisco")
        prefs = _make_prefs(locations=["San Francisco"])
        scores = compute_match_scores(resume, job, prefs)
        assert scores["location_preference"] == 100.0

    def test_location_no_match(self):
        """Job not in preferred locations should get low score."""
        resume = _make_resume(skills=["python"])
        job = _make_job(title="Dev", description="dev", location="London")
        prefs = _make_prefs(locations=["New York"])
        scores = compute_match_scores(resume, job, prefs)
        assert scores["location_preference"] < 50

    def test_remote_preference(self):
        """Remote job should score well if user prefers remote."""
        resume = _make_resume(skills=["python"])
        job = _make_job(title="Dev", description="dev", location="Remote")
        prefs = _make_prefs(remote_preference="remote")
        scores = compute_match_scores(resume, job, prefs)
        assert scores["location_preference"] >= 80

    def test_salary_in_range(self):
        """Job with salary in user's range should score 100."""
        resume = _make_resume(skills=["python"])
        job = _make_job(title="Dev", description="dev", salary_range="$120,000 - $180,000")
        prefs = _make_prefs(salary_min=100000, salary_max=200000)
        scores = compute_match_scores(resume, job, prefs)
        assert scores["salary_preference"] == 100.0

    def test_priority_company(self):
        """Job at a priority company should score 100 on company priority."""
        resume = _make_resume(skills=["python"])
        job = _make_job(title="Dev", description="dev", company="Google")
        prefs = _make_prefs(priority_companies=["Google", "Meta"])
        scores = compute_match_scores(resume, job, prefs)
        assert scores["company_priority"] == 100.0

    def test_total_score_range(self):
        """Total score should always be between 0 and 100."""
        resume = _make_resume(skills=["python", "react"])
        job = _make_job(title="Dev", description="python react", company="Acme")
        prefs = _make_prefs()
        scores = compute_match_scores(resume, job, prefs)
        assert 0 <= scores["total"] <= 100

    def test_no_preferences(self):
        """Matching without preferences should still work with neutral scores."""
        resume = _make_resume(skills=["python"])
        job = _make_job(title="Dev", description="python developer needed")
        scores = compute_match_scores(resume, job, None)
        assert "total" in scores
        assert all(0 <= v <= 100 for v in scores.values())
