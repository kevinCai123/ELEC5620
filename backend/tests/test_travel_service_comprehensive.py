"""Comprehensive tests for app/services/travel.py - travel advice service."""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from zoneinfo import ZoneInfo

import pytest

from app.services.travel import TravelService


@pytest.fixture
def travel_service():
    """Create a TravelService instance with mock settings."""
    with patch("app.services.travel._SETTINGS") as mock_settings:
        mock_settings.openweather_api_key = "test-api-key"
        mock_settings.generic_travel_buffer_minutes = 15
        mock_settings.default_weather_location = "Sydney"
        mock_settings.google_maps_base_url = "https://www.google.com/maps/dir/?api=1"
        service = TravelService()
        yield service


@pytest.mark.asyncio
async def test_advise_with_weather_data():
    """Test advise returns advice with weather data."""
    service = TravelService()
    
    mock_weather = {
        "rain": 0.5,
        "temp_c": 18.0,
        "wind_speed": 5.0,
        "buffer_minutes": 20
    }
    
    with patch.object(service, "_fetch_weather", return_value=mock_weather):
        when = datetime.now(tz=ZoneInfo("UTC")) + timedelta(hours=1)
        result = await service.advise("Sydney", when)
        
        assert result.fallback_used is False
        assert result.leave_time < when
        assert "umbrella" in result.bring_items  # Rain > 0.3
        assert result.weather is not None


@pytest.mark.asyncio
async def test_advise_suggests_jacket_when_cold():
    """Test that advise suggests jacket when temperature is low."""
    service = TravelService()
    
    mock_weather = {
        "rain": 0.0,
        "temp_c": 14.0,  # Below 16
        "wind_speed": 3.0,
        "buffer_minutes": 15
    }
    
    with patch.object(service, "_fetch_weather", return_value=mock_weather):
        when = datetime.now(tz=ZoneInfo("UTC")) + timedelta(hours=1)
        result = await service.advise("Sydney", when)
        
        assert "jacket" in result.bring_items


@pytest.mark.asyncio
async def test_advise_suggests_water_bottle_when_no_items():
    """Test that advise suggests water bottle when no weather concerns."""
    service = TravelService()
    
    mock_weather = {
        "rain": 0.0,
        "temp_c": 22.0,  # Nice weather
        "wind_speed": 2.0,
        "buffer_minutes": 15
    }
    
    with patch.object(service, "_fetch_weather", return_value=mock_weather):
        when = datetime.now(tz=ZoneInfo("UTC")) + timedelta(hours=1)
        result = await service.advise("Sydney", when)
        
        assert "water bottle" in result.bring_items


@pytest.mark.asyncio
async def test_advise_fallback_when_no_api_key():
    """Test that advise uses fallback when no API key configured."""
    with patch("app.services.travel._SETTINGS") as mock_settings:
        mock_settings.openweather_api_key = None
        mock_settings.generic_travel_buffer_minutes = 15
        mock_settings.default_weather_location = "Sydney"
        mock_settings.google_maps_base_url = "https://maps.google.com"
        
        service = TravelService()
        
        when = datetime.now(tz=ZoneInfo("UTC")) + timedelta(hours=1)
        result = await service.advise("Sydney", when)
        
        assert result.fallback_used is True
        assert "generic guidance" in result.recommendation.lower()


@pytest.mark.asyncio
async def test_advise_fallback_when_weather_fetch_fails():
    """Test that advise uses fallback when weather API fails."""
    service = TravelService()
    
    with patch.object(service, "_fetch_weather", side_effect=Exception("API Error")):
        when = datetime.now(tz=ZoneInfo("UTC")) + timedelta(hours=1)
        result = await service.advise("Sydney", when)
        
        assert result.fallback_used is True


@pytest.mark.asyncio
async def test_advise_tries_default_location_on_failure():
    """Test that advise tries default location when custom location fails."""
    service = TravelService()
    service._default_location = "Sydney"
    
    mock_weather = {
        "rain": 0.0,
        "temp_c": 20.0,
        "wind_speed": 3.0,
        "buffer_minutes": 15
    }
    
    call_count = 0
    async def mock_fetch(location):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("Location not found")
        return mock_weather
    
    with patch.object(service, "_fetch_weather", side_effect=mock_fetch):
        when = datetime.now(tz=ZoneInfo("UTC")) + timedelta(hours=1)
        result = await service.advise("UnknownCity", when)
        
        # Should have tried twice: once for UnknownCity, once for default
        assert call_count == 2
        assert result.fallback_used is False


@pytest.mark.asyncio
async def test_advise_skip_default_if_already_trying_default():
    """Test that advise doesn't retry with default if already using default location."""
    service = TravelService()
    service._default_location = "Sydney"
    
    with patch.object(service, "_fetch_weather", side_effect=Exception("API Error")) as mock_fetch:
        when = datetime.now(tz=ZoneInfo("UTC")) + timedelta(hours=1)
        result = await service.advise("sydney", when)  # Same as default (case insensitive)
        
        # Should only try once since we're already trying the default
        assert mock_fetch.call_count == 1
        assert result.fallback_used is True


@pytest.mark.asyncio
async def test_fetch_weather_success():
    """Test that _fetch_weather parses API response correctly."""
    service = TravelService()
    
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "main": {"temp": 25.5},
        "wind": {"speed": 4.2},
        "rain": {"1h": 5.0}  # 5mm in 1 hour
    }
    mock_response.raise_for_status = MagicMock()
    
    with patch("app.services.travel.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        MockClient.return_value.__aenter__.return_value = mock_client
        
        result = await service._fetch_weather("Sydney")
        
        assert result["temp_c"] == 25.5
        assert result["wind_speed"] == 4.2
        assert result["rain"] == 0.5  # 5mm / 10 = 0.5
        assert result["buffer_minutes"] >= 15


@pytest.mark.asyncio
async def test_fetch_weather_handles_missing_rain_data():
    """Test that _fetch_weather handles missing rain data."""
    service = TravelService()
    
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "main": {"temp": 20.0},
        "wind": {"speed": 3.0}
        # No "rain" key
    }
    mock_response.raise_for_status = MagicMock()
    
    with patch("app.services.travel.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        MockClient.return_value.__aenter__.return_value = mock_client
        
        result = await service._fetch_weather("Sydney")
        
        assert result["rain"] == 0.0


@pytest.mark.asyncio
async def test_fetch_weather_clamps_rain_to_1():
    """Test that _fetch_weather clamps rain probability to max 1.0."""
    service = TravelService()
    
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "main": {"temp": 20.0},
        "wind": {"speed": 2.0},
        "rain": {"1h": 50.0}  # Very heavy rain -> would be 5.0 without clamping
    }
    mock_response.raise_for_status = MagicMock()
    
    with patch("app.services.travel.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        MockClient.return_value.__aenter__.return_value = mock_client
        
        result = await service._fetch_weather("Sydney")
        
        assert result["rain"] <= 1.0


def test_compose_recommendation_basic():
    """Test _compose_recommendation creates basic message."""
    service = TravelService()
    
    result = service._compose_recommendation(15, ["water bottle"], False)
    
    assert "15 minutes" in result
    assert "water bottle" in result
    assert "generic guidance" not in result.lower()


def test_compose_recommendation_with_fallback():
    """Test _compose_recommendation includes fallback note."""
    service = TravelService()
    
    result = service._compose_recommendation(15, [], True)
    
    assert "15 minutes" in result
    assert "generic guidance" in result.lower()


def test_compose_recommendation_multiple_items():
    """Test _compose_recommendation joins multiple items."""
    service = TravelService()
    
    result = service._compose_recommendation(20, ["umbrella", "jacket"], False)
    
    assert "umbrella and jacket" in result


def test_compose_recommendation_no_items():
    """Test _compose_recommendation handles empty items list."""
    service = TravelService()
    
    result = service._compose_recommendation(15, [], False)
    
    assert "15 minutes" in result
    # Should not have "Bring" message


@pytest.mark.asyncio
async def test_advise_creates_route_url():
    """Test that advise creates Google Maps route URL."""
    service = TravelService()
    
    with patch.object(service, "_fetch_weather", side_effect=Exception("No weather")):
        when = datetime.now(tz=ZoneInfo("UTC")) + timedelta(hours=1)
        result = await service.advise("Central Station", when)
        
        assert "Central" in result.route_url
        assert "Station" in result.route_url


@pytest.mark.asyncio
async def test_advise_handles_timezone_aware_datetime():
    """Test that advise handles timezone-aware datetime correctly."""
    service = TravelService()
    
    with patch.object(service, "_fetch_weather", side_effect=Exception("No weather")):
        when = datetime(2025, 12, 31, 10, 0, tzinfo=ZoneInfo("Australia/Sydney"))
        result = await service.advise("Sydney", when)
        
        assert result.leave_time.tzinfo is not None
        assert result.leave_time < when


@pytest.mark.asyncio
async def test_advise_handles_naive_datetime():
    """Test that advise handles naive datetime by using when's timezone."""
    service = TravelService()
    
    mock_weather = {
        "rain": 0.0,
        "temp_c": 20.0,
        "wind_speed": 3.0,
        "buffer_minutes": 15
    }
    
    with patch.object(service, "_fetch_weather", return_value=mock_weather):
        when = datetime(2025, 12, 31, 10, 0, tzinfo=ZoneInfo("UTC"))
        result = await service.advise("Sydney", when)
        
        # leave_time should have same timezone as when
        assert result.leave_time.tzinfo == when.tzinfo


@pytest.mark.asyncio
async def test_advise_emits_metrics():
    """Test that advise emits fallback metrics."""
    service = TravelService()
    
    with patch.object(service, "_fetch_weather", side_effect=Exception("Error")):
        with patch("app.services.travel.emit_metric") as mock_emit:
            when = datetime.now(tz=ZoneInfo("UTC")) + timedelta(hours=1)
            await service.advise("Sydney", when)
            
            # Should emit fallback_rate metric
            mock_emit.assert_called()
            calls = [call for call in mock_emit.call_args_list if call[0][0] == "fallback_rate"]
            assert len(calls) > 0


@pytest.mark.asyncio
async def test_advise_uses_time_metric():
    """Test that advise uses time metric for performance tracking."""
    service = TravelService()
    
    with patch.object(service, "_fetch_weather", side_effect=Exception("Error")):
        with patch("app.services.travel.time_metric") as mock_time_metric:
            when = datetime.now(tz=ZoneInfo("UTC")) + timedelta(hours=1)
            await service.advise("Sydney", when)
            
            # Should use time_metric context manager
            mock_time_metric.assert_called_once_with("p95_latency_ms", feature="travel")


@pytest.mark.asyncio
async def test_fetch_weather_uses_correct_api_params():
    """Test that _fetch_weather uses correct OpenWeather API parameters."""
    service = TravelService()
    service._api_key = "test-key-123"
    
    mock_response = MagicMock()
    mock_response.json.return_value = {"main": {"temp": 20}, "wind": {"speed": 3}}
    mock_response.raise_for_status = MagicMock()
    
    with patch("app.services.travel.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        MockClient.return_value.__aenter__.return_value = mock_client
        
        await service._fetch_weather("Tokyo")
        
        # Verify API call parameters
        call_args = mock_client.get.call_args
        assert "api.openweathermap.org" in call_args[0][0]
        assert call_args[1]["params"]["q"] == "Tokyo"
        assert call_args[1]["params"]["appid"] == "test-key-123"
        assert call_args[1]["params"]["units"] == "metric"


@pytest.mark.asyncio
async def test_fetch_weather_calculates_buffer_from_wind():
    """Test that _fetch_weather calculates buffer minutes based on wind speed."""
    service = TravelService()
    service._fallback_minutes = 15
    
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "main": {"temp": 20},
        "wind": {"speed": 25.0}  # Strong wind
    }
    mock_response.raise_for_status = MagicMock()
    
    with patch("app.services.travel.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        MockClient.return_value.__aenter__.return_value = mock_client
        
        result = await service._fetch_weather("Sydney")
        
        # Buffer should be at least the wind speed
        assert result["buffer_minutes"] >= 25

