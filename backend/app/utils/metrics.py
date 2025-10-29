from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from typing import Iterator

logger = logging.getLogger("metrics")


def emit_metric(name: str, value: float, **extra: object) -> None:
    payload = {"metric": name, "value": value}
    if extra:
        payload.update(extra)
    logger.info("metric", extra=payload)


@contextmanager
def time_metric(name: str, **extra: object) -> Iterator[None]:
    start = time.perf_counter()
    yield
    duration_ms = (time.perf_counter() - start) * 1000
    emit_metric(name, round(duration_ms, 2), **extra)


__all__ = ["emit_metric", "time_metric"]
