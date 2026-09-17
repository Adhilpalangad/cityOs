import time
import uuid

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

SERVICE_NAME = "city-core"


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex}"
        request.state.request_id = request_id
        started = time.perf_counter()
        structlog.contextvars.bind_contextvars(request_id=request_id, service=SERVICE_NAME)
        try:
            response = await call_next(request)
        finally:
            structlog.contextvars.clear_contextvars()
        response.headers["X-Request-ID"] = request_id
        structlog.get_logger().info(
            "request_completed",
            request_id=request_id,
            service=SERVICE_NAME,
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round((time.perf_counter() - started) * 1000, 2),
        )
        return response
