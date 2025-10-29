from __future__ import annotations
import time
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request, Response
from pythonjsonlogger import jsonlogger
from starlette.middleware.base import BaseHTTPMiddleware


def configure_logging() -> None:
    """Configure JSON logging for the application."""
    formatter = jsonlogger.JsonFormatter("%(message)s")
    import logging
    import sys

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(logging.INFO)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that enriches requests with a request_id and logs duration."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = str(uuid.uuid4())
        start = time.perf_counter()

        # Attach request_id to scope for downstream usage
        request.state.request_id = request_id

        response_status = 500
        response: Response | None = None
        error_payload: dict[str, Any] | None = None
        try:
            response = await call_next(request)
            response_status = response.status_code
            return response
        except Exception as exc:  # noqa: BLE001
            import logging

            error_payload = {"error": type(exc).__name__}
            logging.getLogger(__name__).exception("Unhandled error", extra={"request_id": request_id})
            raise
        finally:
            latency_ms = (time.perf_counter() - start) * 1000
            log_payload = {
                "ts": time.time(),
                "request_id": request_id,
                "route": request.url.path,
                "method": request.method,
                "status": response_status,
                "latency_ms": round(latency_ms, 2),
                "user_agent": request.headers.get("user-agent", "unknown"),
            }
            if error_payload:
                log_payload.update(error_payload)
            fallback_used = getattr(request.state, "fallback_used", False)
            if fallback_used:
                log_payload["fallback_used"] = True

            import logging

            logging.getLogger("request").info(
                "request_completed",
                extra=log_payload,
            )


__all__ = ["configure_logging", "RequestLoggingMiddleware"]
