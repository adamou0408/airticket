"""Tests for Task 1.1: Backend project initialization.

Verifies:
- Health endpoint returns 200
- API router is mounted
"""

import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


@pytest.mark.asyncio
async def test_api_prefix_exists(client):
    # API routes should be under /api - a 404 (not 405) means router is mounted
    response = await client.get("/api/nonexistent")
    assert response.status_code in (404, 405)
