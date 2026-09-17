"""Reverse proxy from the gateway to downstream services.

Module 02 introduced the first downstream service, `identity`; Module 03
adds `city-core`. The gateway forwards each service's routes verbatim --
method, headers, query string, and body -- and relays the response back
unmodified, including redirects (OAuth's `/authorize` endpoints return a
302 the browser must follow itself, so this proxy never follows redirects
on the caller's behalf). Adding a new downstream service is one entry in
`_SERVICES` below; this file stays a thin transport concern, never a place
for business logic.
"""

from collections.abc import Callable

import httpx
from fastapi import APIRouter, Request, Response

from app.core.config import Settings, get_settings

router = APIRouter()

# path prefix -> the Settings attribute holding that service's base URL.
_SERVICES: dict[tuple[str, ...], str] = {
    (
        "/api/v1/auth",
        "/api/v1/users",
        "/api/v1/roles",
        "/api/v1/departments",
        "/api/v1/permissions",
    ): "identity_service_url",
    (
        "/api/v1/roads",
        "/api/v1/hospitals",
        "/api/v1/vehicles",
        "/api/v1/incidents",
        "/api/v1/routes",
        "/api/v1/stops",
        "/api/v1/water",
        "/api/v1/energy",
        "/api/v1/environment",
        "/api/v1/infrastructure",
        "/api/v1/projects",
        "/api/v1/complaints",
        "/api/v1/workflows",
        "/api/v1/audit",
        "/api/v1/notifications",
        "/api/v1/simulations",
        "/api/v1/ai",
        "/api/v1/knowledge",
        "/api/v1/search",
        "/api/v1/analytics",
    ): "city_core_service_url",
}

_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]

# Hop-by-hop headers (RFC 7230 §6.1) plus Host/Content-Length, which must be
# recomputed for the upstream request rather than copied verbatim.
_HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "host",
    "content-length",
}


def _filtered_headers(items) -> dict[str, str]:
    return {key: value for key, value in items if key.lower() not in _HOP_BY_HOP_HEADERS}


def _make_proxy_handler(upstream_url_attr: str) -> Callable[..., Response]:
    async def handler(request: Request, rest: str | None = None) -> Response:
        settings: Settings = get_settings()
        upstream_base = getattr(settings, upstream_url_attr)
        upstream_url = f"{upstream_base}{request.url.path}"
        body = await request.body()
        async with httpx.AsyncClient(follow_redirects=False, timeout=10) as client:
            upstream_response = await client.request(
                request.method,
                upstream_url,
                params=request.url.query,
                headers=_filtered_headers(request.headers.items()),
                content=body,
            )
        return Response(
            content=upstream_response.content,
            status_code=upstream_response.status_code,
            headers=_filtered_headers(upstream_response.headers.items()),
        )

    return handler


for _prefixes, _upstream_url_attr in _SERVICES.items():
    _handler = _make_proxy_handler(_upstream_url_attr)
    for _prefix in _prefixes:
        router.add_api_route(_prefix, _handler, methods=_METHODS, include_in_schema=False)
        router.add_api_route(
            f"{_prefix}/{{rest:path}}", _handler, methods=_METHODS, include_in_schema=False
        )
