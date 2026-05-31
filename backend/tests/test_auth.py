"""
Tests for auth endpoints: register, login, me.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """Registration should return a JWT token."""
    response = await client.post("/api/auth/register", json={
        "email": "newuser@example.com",
        "password": "securepass",
        "name": "New User",
    })
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Registering with an existing email should fail."""
    payload = {
        "email": "dupe@example.com",
        "password": "securepass",
        "name": "User 1",
    }
    await client.post("/api/auth/register", json=payload)
    response = await client.post("/api/auth/register", json=payload)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient):
    """Registration with a short password should fail validation."""
    response = await client.post("/api/auth/register", json={
        "email": "weak@example.com",
        "password": "12",
        "name": "Weak",
    })
    assert response.status_code == 422  # Pydantic validation error


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Login with valid credentials should return a token."""
    await client.post("/api/auth/register", json={
        "email": "login@example.com",
        "password": "mypassword",
        "name": "Login User",
    })
    response = await client.post("/api/auth/login", json={
        "email": "login@example.com",
        "password": "mypassword",
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    """Login with wrong password should return 401."""
    await client.post("/api/auth/register", json={
        "email": "wrongpw@example.com",
        "password": "correctpass",
        "name": "User",
    })
    response = await client.post("/api/auth/login", json={
        "email": "wrongpw@example.com",
        "password": "wrongpass",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_authenticated(client: AsyncClient, auth_headers: dict):
    """GET /me with valid token should return user info."""
    response = await client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"


@pytest.mark.asyncio
async def test_me_unauthenticated(client: AsyncClient):
    """GET /me without a token should return 401 or 403."""
    response = await client.get("/api/auth/me")
    assert response.status_code in (401, 403)
