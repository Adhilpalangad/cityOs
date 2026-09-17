"""WebSocket relay from the gateway to city-core's live feed.

`app/api/proxy.py` forwards plain HTTP request/response pairs one at a time
via `httpx`; a WebSocket needs a persistent bidirectional pipe instead, which
`httpx` doesn't speak, so this stays a small separate module rather than
another entry in `proxy.py`'s `_SERVICES` map. The browser connects to this
gateway route; the gateway opens its own outbound connection to city-core's
`/ws/live` (see services/city-core/app/api/routes_live.py) and pumps messages
between the two until either side disconnects.
"""

import asyncio

import structlog
import websockets
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from websockets.exceptions import ConnectionClosed

from app.core.config import get_settings

router = APIRouter()
logger = structlog.get_logger()


def _upstream_ws_url(token: str | None) -> str:
    settings = get_settings()
    base = settings.city_core_service_url.replace("http://", "ws://", 1).replace(
        "https://", "wss://", 1
    )
    url = f"{base}/ws/live"
    return f"{url}?token={token}" if token else url


@router.websocket("/ws/live")
async def live_feed_proxy(ws: WebSocket, token: str | None = None) -> None:
    await ws.accept()
    try:
        async with websockets.connect(_upstream_ws_url(token)) as upstream:

            async def relay_downstream() -> None:
                async for message in upstream:
                    if isinstance(message, bytes):
                        message = message.decode()
                    await ws.send_text(message)

            async def relay_upstream() -> None:
                while True:
                    message = await ws.receive_text()
                    await upstream.send(message)

            downstream_task = asyncio.create_task(relay_downstream())
            upstream_task = asyncio.create_task(relay_upstream())
            try:
                await asyncio.wait(
                    [downstream_task, upstream_task], return_when=asyncio.FIRST_COMPLETED
                )
            finally:
                downstream_task.cancel()
                upstream_task.cancel()
    except (ConnectionClosed, OSError) as exc:
        logger.warning("live_feed_proxy_upstream_unavailable", error=str(exc))
    except WebSocketDisconnect:
        pass
    finally:
        try:
            await ws.close()
        except RuntimeError:
            # Already closed by the client disconnecting.
            pass
