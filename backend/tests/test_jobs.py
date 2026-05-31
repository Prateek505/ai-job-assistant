"""
Tests for job listing and management endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_jobs_empty(client: AsyncClient, auth_headers: dict):
    """Listing jobs when none exist should return empty list."""
    response = await client.get("/api/jobs/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_and_list_job(client: AsyncClient, auth_headers: dict):
    """Creating a job and then listing should show it."""
    create_resp = await client.post("/api/jobs/", headers=auth_headers, json={
        "title": "Senior Python Developer",
        "company": "TechCorp",
        "description": "We need a Python expert with FastAPI experience.",
        "location": "Remote",
        "salary_range": "$120,000 - $180,000",
    })
    assert create_resp.status_code == 201
    job_data = create_resp.json()
    assert job_data["title"] == "Senior Python Developer"
    assert job_data["company"] == "TechCorp"

    list_resp = await client.get("/api/jobs/", headers=auth_headers)
    assert list_resp.status_code == 200
    jobs = list_resp.json()
    assert len(jobs) >= 1
    assert any(j["title"] == "Senior Python Developer" for j in jobs)


@pytest.mark.asyncio
async def test_get_job_by_id(client: AsyncClient, auth_headers: dict):
    """Getting a job by ID should return its details."""
    create_resp = await client.post("/api/jobs/", headers=auth_headers, json={
        "title": "Frontend Engineer",
        "company": "WebCo",
        "description": "React and TypeScript expert needed.",
    })
    job_id = create_resp.json()["id"]

    response = await client.get(f"/api/jobs/{job_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["title"] == "Frontend Engineer"


@pytest.mark.asyncio
async def test_get_job_not_found(client: AsyncClient, auth_headers: dict):
    """Getting a non-existent job should return 404."""
    response = await client.get("/api/jobs/99999", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_search_jobs(client: AsyncClient, auth_headers: dict):
    """Searching jobs should filter by keyword."""
    await client.post("/api/jobs/", headers=auth_headers, json={
        "title": "Data Scientist",
        "company": "DataCorp",
        "description": "ML and statistics expert.",
    })
    await client.post("/api/jobs/", headers=auth_headers, json={
        "title": "DevOps Engineer",
        "company": "CloudInc",
        "description": "Infrastructure and CI/CD.",
    })

    response = await client.get("/api/jobs/?search=Data", headers=auth_headers)
    assert response.status_code == 200
    jobs = response.json()
    assert all("Data" in j["title"] or "data" in j["description"].lower() for j in jobs)
