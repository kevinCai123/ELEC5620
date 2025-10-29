from __future__ import annotations

import asyncio
import json
import os
import time
from collections.abc import Awaitable, Callable
from functools import wraps
from hashlib import sha256
import pickle
from typing import Any, TypeVar

try:  # Optional dependency
    import aioredis  # type: ignore
except ImportError:  # pragma: no cover
    aioredis = None  # type: ignore

ReturnType = TypeVar("ReturnType")

_memory_cache: dict[str, tuple[float, Any]] = {}
_lock = asyncio.Lock()


def _make_key(name: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
    """Create a deterministic cache key."""
    key_payload = {
        "fn": name,
        "args": [repr(arg) for arg in args],
        "kwargs": {k: repr(v) for k, v in sorted(kwargs.items())},
    }
    digest = sha256(json.dumps(key_payload, sort_keys=True).encode("utf-8")).hexdigest()
    return digest


async def _get_redis_client() -> Any | None:
    url = os.getenv("REDIS_URL")
    if not url or aioredis is None:
        return None
    return await aioredis.from_url(url, encoding=None, decode_responses=False)  # type: ignore[arg-type]


def cache(ttl: int = 86400) -> Callable[[Callable[..., Awaitable[ReturnType]]], Callable[..., Awaitable[ReturnType]]]:
    """Async cache decorator with optional Redis backing."""

    def decorator(fn: Callable[..., Awaitable[ReturnType]]) -> Callable[..., Awaitable[ReturnType]]:
        if not asyncio.iscoroutinefunction(fn):
            msg = "@cache decorator can only be used with async functions"
            raise TypeError(msg)

        @wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> ReturnType:
            key = _make_key(fn.__name__, args[1:], kwargs)  # drop self reference
            now = time.time()

            async with _lock:
                entry = _memory_cache.get(key)
                if entry and entry[0] > now:
                    return entry[1]

            client = await _get_redis_client()
            if client:
                cached_value = await client.get(key)
                if cached_value is not None:
                    try:
                        return pickle.loads(cached_value)
                    except Exception:  # pragma: no cover - corrupted cache
                        await client.delete(key)

            result = await fn(*args, **kwargs)

            async with _lock:
                _memory_cache[key] = (now + ttl, result)

            if client:
                try:
                    await client.set(key, pickle.dumps(result), ex=ttl)
                except Exception:  # pragma: no cover - serialization issue
                    await client.delete(key)

            return result

        return wrapper

    return decorator


__all__ = ["cache"]
