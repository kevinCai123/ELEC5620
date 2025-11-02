"""Tests for app/services/cache.py - caching decorator."""
from __future__ import annotations

import asyncio
import os
import pickle
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.cache import _make_key, cache


def test_make_key_creates_deterministic_key():
    """Test that _make_key creates consistent keys for same inputs."""
    key1 = _make_key("test_func", (1, "arg"), {"kwarg": "value"})
    key2 = _make_key("test_func", (1, "arg"), {"kwarg": "value"})
    assert key1 == key2
    assert len(key1) == 64  # SHA256 hex digest


def test_make_key_different_for_different_inputs():
    """Test that _make_key creates different keys for different inputs."""
    key1 = _make_key("test_func", (1,), {})
    key2 = _make_key("test_func", (2,), {})
    assert key1 != key2


def test_make_key_handles_kwargs_order():
    """Test that _make_key is consistent regardless of kwargs order."""
    key1 = _make_key("test_func", (), {"a": 1, "b": 2})
    key2 = _make_key("test_func", (), {"b": 2, "a": 1})
    assert key1 == key2


def test_cache_decorator_raises_on_non_async_function():
    """Test that cache decorator raises TypeError for non-async functions."""
    with pytest.raises(TypeError, match="async functions"):
        @cache(ttl=60)
        def sync_function():
            return "result"


@pytest.mark.asyncio
async def test_cache_decorator_caches_result():
    """Test that cache decorator caches async function results."""
    call_count = 0

    @cache(ttl=60)
    async def test_func(self, arg: int) -> int:
        nonlocal call_count
        call_count += 1
        return arg * 2

    class DummySelf:
        pass

    dummy = DummySelf()
    
    # First call should execute function
    result1 = await test_func(dummy, 5)
    assert result1 == 10
    assert call_count == 1

    # Second call should use cache
    result2 = await test_func(dummy, 5)
    assert result2 == 10
    assert call_count == 1  # Not called again


@pytest.mark.asyncio
async def test_cache_decorator_expires_after_ttl():
    """Test that cached values expire after TTL."""
    from app.services.cache import _memory_cache
    _memory_cache.clear()  # Clear cache before test
    
    call_count = 0

    @cache(ttl=1)  # 1 second TTL
    async def test_func(self, arg: int) -> int:
        nonlocal call_count
        call_count += 1
        return arg * 2

    class DummySelf:
        pass

    dummy = DummySelf()
    
    # First call
    result1 = await test_func(dummy, 5)
    assert result1 == 10
    assert call_count == 1

    # Wait for TTL to expire
    await asyncio.sleep(1.2)

    # Should call function again
    result2 = await test_func(dummy, 5)
    assert result2 == 10
    assert call_count == 2


@pytest.mark.asyncio
async def test_cache_decorator_different_args_different_cache():
    """Test that different arguments result in different cache entries."""
    from app.services.cache import _memory_cache
    _memory_cache.clear()  # Clear cache before test
    
    call_count = 0

    @cache(ttl=60)
    async def test_func(self, arg: int) -> int:
        nonlocal call_count
        call_count += 1
        return arg * 2

    class DummySelf:
        pass

    dummy = DummySelf()
    
    result1 = await test_func(dummy, 5)
    assert result1 == 10
    assert call_count == 1

    result2 = await test_func(dummy, 10)
    assert result2 == 20
    assert call_count == 2


@pytest.mark.asyncio
async def test_cache_with_redis_available():
    """Test caching with Redis available."""
    from app.services.cache import _memory_cache
    _memory_cache.clear()
    
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = None
    
    with patch("app.services.cache._get_redis_client", return_value=mock_redis):
        @cache(ttl=60)
        async def test_func(self, arg: int) -> int:
            return arg * 2

        class DummySelf:
            pass

        dummy = DummySelf()
        result = await test_func(dummy, 5)
        
        assert result == 10
        assert mock_redis.get.called
        assert mock_redis.set.called


@pytest.mark.asyncio
async def test_cache_retrieves_from_redis():
    """Test that cache retrieves values from Redis."""
    from app.services.cache import _memory_cache
    _memory_cache.clear()
    
    cached_value = pickle.dumps(42)
    mock_redis = AsyncMock()
    mock_redis.get.return_value = cached_value
    
    call_count = 0

    with patch("app.services.cache._get_redis_client", return_value=mock_redis):
        @cache(ttl=60)
        async def test_func(self, arg: int) -> int:
            nonlocal call_count
            call_count += 1
            return arg * 2

        class DummySelf:
            pass

        dummy = DummySelf()
        result = await test_func(dummy, 5)
        
        assert result == 42  # From cache, not calculated
        assert call_count == 0  # Function not called
        assert mock_redis.get.called


@pytest.mark.asyncio
async def test_cache_handles_redis_corrupted_value():
    """Test that cache handles corrupted Redis values gracefully."""
    from app.services.cache import _memory_cache
    _memory_cache.clear()
    
    mock_redis = AsyncMock()
    mock_redis.get.return_value = b"corrupted data"
    mock_redis.delete.return_value = None
    mock_redis.set.return_value = None
    
    with patch("app.services.cache._get_redis_client", return_value=mock_redis):
        @cache(ttl=60)
        async def test_func(self, arg: int) -> int:
            return arg * 2

        class DummySelf:
            pass

        dummy = DummySelf()
        result = await test_func(dummy, 5)
        
        assert result == 10  # Falls back to computing
        # delete called at least once (for corrupted value)
        assert mock_redis.delete.call_count >= 1


@pytest.mark.asyncio
async def test_get_redis_client_returns_none_without_url():
    """Test that _get_redis_client returns None when REDIS_URL not set."""
    from app.services.cache import _get_redis_client
    
    with patch.dict(os.environ, {}, clear=True):
        client = await _get_redis_client()
        assert client is None


@pytest.mark.asyncio
async def test_get_redis_client_returns_none_without_aioredis():
    """Test that _get_redis_client returns None when aioredis not available."""
    from app.services.cache import _get_redis_client
    
    with patch.dict(os.environ, {"REDIS_URL": "redis://localhost"}):
        with patch("app.services.cache.aioredis", None):
            client = await _get_redis_client()
            assert client is None


@pytest.mark.asyncio
async def test_cache_with_kwargs():
    """Test that cache works correctly with keyword arguments."""
    call_count = 0

    @cache(ttl=60)
    async def test_func(self, arg: int, multiplier: int = 2) -> int:
        nonlocal call_count
        call_count += 1
        return arg * multiplier

    class DummySelf:
        pass

    dummy = DummySelf()
    
    result1 = await test_func(dummy, 5, multiplier=3)
    assert result1 == 15
    assert call_count == 1

    result2 = await test_func(dummy, 5, multiplier=3)
    assert result2 == 15
    assert call_count == 1  # Cached

    result3 = await test_func(dummy, 5, multiplier=4)
    assert result3 == 20
    assert call_count == 2  # Different kwargs


@pytest.mark.asyncio
async def test_cache_memory_cache_is_shared():
    """Test that memory cache is shared across function calls."""
    from app.services.cache import _memory_cache
    
    # Clear cache first
    _memory_cache.clear()
    
    @cache(ttl=60)
    async def test_func(self, arg: int) -> int:
        return arg * 2

    class DummySelf:
        pass

    dummy = DummySelf()
    
    assert len(_memory_cache) == 0
    await test_func(dummy, 5)
    assert len(_memory_cache) == 1

