"""Health check endpoint tests."""

from unittest.mock import AsyncMock, MagicMock, patch

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
async def test_health_check_healthy(simple_client: AsyncClient):
    """Test that health check returns OK when all services are healthy."""
    with (
        patch("main.engine") as mock_engine,
        patch("main.get_redis") as mock_get_redis,
    ):
        # Mock DB connection
        mock_conn = MagicMock()
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)
        mock_conn.execute = AsyncMock()
        mock_engine.connect.return_value = mock_conn

        # Mock Redis
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_get_redis.return_value = mock_redis

        response = await simple_client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_health_check_response_structure(simple_client: AsyncClient):
    """Test that health check response has expected structure."""
    with (
        patch("main.engine") as mock_engine,
        patch("main.get_redis") as mock_get_redis,
    ):
        mock_conn = MagicMock()
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)
        mock_conn.execute = AsyncMock()
        mock_engine.connect.return_value = mock_conn

        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_get_redis.return_value = mock_redis

        response = await simple_client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "services" in data
    assert "database" in data["services"]
    assert "redis" in data["services"]


@pytest.mark.asyncio
async def test_health_check_degraded_db(simple_client: AsyncClient):
    """Test that health check reports degraded when DB is down."""
    with (
        patch("main.engine") as mock_engine,
        patch("main.get_redis") as mock_get_redis,
    ):
        mock_conn = MagicMock()
        mock_conn.__aenter__ = AsyncMock(side_effect=Exception("DB connection failed"))
        mock_conn.__aexit__ = AsyncMock(return_value=None)
        mock_engine.connect.return_value = mock_conn

        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_get_redis.return_value = mock_redis

        response = await simple_client.get("/health")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "degraded"
    assert data["services"]["database"] == "error"


@pytest.mark.asyncio
async def test_health_check_degraded_redis(simple_client: AsyncClient):
    """Test that health check reports degraded when Redis is down."""
    with (
        patch("main.engine") as mock_engine,
        patch("main.get_redis") as mock_get_redis,
    ):
        mock_conn = MagicMock()
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)
        mock_conn.execute = AsyncMock()
        mock_engine.connect.return_value = mock_conn

        mock_get_redis.side_effect = Exception("Redis connection failed")

        response = await simple_client.get("/health")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "degraded"
    assert data["services"]["redis"] == "error"
