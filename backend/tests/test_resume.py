"""
Tests for resume upload and listing endpoints.
"""

import io
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_resumes_empty(client: AsyncClient, auth_headers: dict):
    """Listing resumes for a new user should return empty list."""
    response = await client.get("/api/resumes/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_upload_invalid_file_type(client: AsyncClient, auth_headers: dict):
    """Uploading a non-PDF/DOCX file should fail."""
    response = await client.post(
        "/api/resumes/upload",
        headers=auth_headers,
        files={"file": ("test.txt", b"Some text content", "text/plain")},
    )
    assert response.status_code == 400
    assert "PDF and DOCX" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_resume_not_found(client: AsyncClient, auth_headers: dict):
    """Getting a non-existent resume should return 404."""
    response = await client.get("/api/resumes/99999", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_resume_upload_unauthenticated(client: AsyncClient):
    """Uploading without auth should return 401 or 403."""
    response = await client.post(
        "/api/resumes/upload",
        files={"file": ("test.pdf", b"fake pdf", "application/pdf")},
    )
    assert response.status_code in (401, 403)
