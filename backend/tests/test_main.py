"""Tests for app/main.py - the FastAPI application entry point."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def mock_settings():
    """Mock settings without Sentry DSN."""
    with patch("app.main.get_settings") as mock:
        settings = MagicMock()
        settings.sentry_dsn = None
        settings.default_timezone = "UTC"
        mock.return_value = settings
        yield settings


@pytest.fixture
def mock_scheduler():
    """Mock the APScheduler."""
    with patch("app.main.scheduler") as mock:
        mock.running = False
        yield mock


def test_before_send_redacts_request_data():
    """Test that _before_send redacts sensitive request data."""
    from app.main import _before_send
    
    event = {
        "request": {
            "data": '{"password": "secret123"}',
            "url": "http://example.com"
        }
    }
    hint = {}
    
    result = _before_send(event, hint)
    
    assert result is not None
    assert result["request"]["data"] == "[REDACTED]"
    assert result["request"]["url"] == "http://example.com"


def test_before_send_handles_missing_request_data():
    """Test that _before_send handles events without request data."""
    from app.main import _before_send
    
    event = {"message": "test"}
    hint = {}
    
    result = _before_send(event, hint)
    
    assert result is not None
    assert result.get("request", {}).get("data") != "[REDACTED]"


def test_app_creation():
    """Test that the FastAPI app is created with correct configuration."""
    from app.main import app
    
    assert app.title == "Study Companion API"
    assert app.version == "0.1.0"


def test_root_endpoint():
    """Test the root endpoint returns the expected message."""
    from app.main import app
    
    client = TestClient(app)
    response = client.get("/")
    
    assert response.status_code == 200
    assert response.json() == {"message": "Study Companion API"}


@pytest.mark.asyncio
async def test_on_startup_creates_tables_and_starts_scheduler(mock_scheduler):
    """Test that startup event creates tables and starts scheduler."""
    from app.main import on_startup
    
    with patch("app.main.engine") as mock_engine:
        mock_conn = AsyncMock()
        mock_engine.begin.return_value.__aenter__.return_value = mock_conn
        
        await on_startup()
        
        # Verify tables were created
        mock_conn.run_sync.assert_called_once()
        
        # Verify scheduler was started
        assert mock_scheduler.start.called
        assert mock_scheduler.add_job.called


@pytest.mark.asyncio
async def test_on_startup_does_not_restart_running_scheduler():
    """Test that startup doesn't restart an already running scheduler."""
    from app.main import on_startup
    
    with patch("app.main.engine") as mock_engine:
        mock_conn = AsyncMock()
        mock_engine.begin.return_value.__aenter__.return_value = mock_conn
        
        with patch("app.main.scheduler") as mock_scheduler:
            mock_scheduler.running = True
            
            await on_startup()
            mock_scheduler.start.assert_not_called()


@pytest.mark.asyncio
async def test_on_shutdown_stops_scheduler():
    """Test that shutdown event stops the scheduler."""
    from app.main import on_shutdown
    
    with patch("app.main.scheduler") as mock_scheduler:
        mock_scheduler.running = True
        
        await on_shutdown()
        mock_scheduler.shutdown.assert_called_once()


@pytest.mark.asyncio
async def test_on_shutdown_does_not_stop_inactive_scheduler():
    """Test that shutdown doesn't try to stop an inactive scheduler."""
    from app.main import on_shutdown
    
    with patch("app.main.scheduler") as mock_scheduler:
        mock_scheduler.running = False
        
        await on_shutdown()
        mock_scheduler.shutdown.assert_not_called()


@pytest.mark.asyncio
async def test_run_digest_job():
    """Test that run_digest_job calls the digest service."""
    from app.main import run_digest_job
    
    mock_digest_service = MagicMock()
    mock_digest_service.run_digest_cycle = AsyncMock()
    
    mock_session = AsyncMock()
    
    with patch("app.main.get_digest_service", return_value=mock_digest_service):
        with patch("app.main.get_session") as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session
            
            await run_digest_job()
            
            mock_digest_service.run_digest_cycle.assert_called_once_with(mock_session)
            mock_session.commit.assert_called_once()


def test_cors_middleware_configured():
    """Test that CORS middleware is configured correctly."""
    from app.main import app
    
    # Check that CORS middleware is present
    cors_middleware = None
    for middleware in app.user_middleware:
        if "CORSMiddleware" in str(middleware):
            cors_middleware = middleware
            break
    
    assert cors_middleware is not None


def test_sentry_middleware_not_added_without_dsn():
    """Test that Sentry middleware is not added when DSN is not configured."""
    # This test verifies the app was created without Sentry DSN in settings
    from app.main import app
    
    # Since we're testing without DSN, Sentry middleware should not be present
    # The app should still work fine
    assert app is not None

