"""Health check endpoint tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.fixture
async def simple_client():
    """Create test client without database dependency."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_check_returns_ok(simple_client: AsyncClient):
    """Test that health check returns OK status."""
    response = await simple_client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_health_check_response_structure(simple_client: AsyncClient):
    """Test that health check response has expected structure."""
    response = await simple_client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
