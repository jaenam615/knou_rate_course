"""Health check endpoint tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test that health check endpoint returns OK."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_health_check_includes_services(client: AsyncClient):
    """Test that health check includes service status."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    # After we add DB/Redis checks, these should be present
    assert "status" in data
