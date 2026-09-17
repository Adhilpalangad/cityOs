"""CityOS Weather Data Provider.

Generates realistic weather readings with correlated rainfall/temperature
patterns and flood-risk alerts.
"""

import asyncio
import math
import random
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

ZONES = ["ZONE-NORTH", "ZONE-SOUTH", "ZONE-CENTRAL", "ZONE-HARBOR", "ZONE-EAST"]

weather_state: dict[str, dict[str, Any]] = {}


def _init() -> None:
    for zone in ZONES:
        weather_state[zone] = {
            "zone": zone,
            "temperature_c": round(random.uniform(26, 34), 1),
            "rainfall_mm": round(random.uniform(0, 10), 2),
            "humidity_pct": round(random.uniform(60, 90), 1),
            "wind_kmh": round(random.uniform(5, 25), 1),
            "aqi": random.randint(30, 80),
            "flood_risk": "LOW",
            "alert": None,
        }


def _flood_risk(rainfall_mm: float) -> str:
    if rainfall_mm < 10:
        return "LOW"
    elif rainfall_mm < 30:
        return "MEDIUM"
    elif rainfall_mm < 60:
        return "HIGH"
    return "CRITICAL"


def _tick() -> list[dict[str, Any]]:
    hour = time.localtime().tm_hour
    # Kerala-inspired monsoon pattern: peak rainfall in evening hours
    rain_factor = 1.0 + 1.5 * math.exp(-((hour - 15) ** 2) / 8)
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    events = []
    for zone, state in weather_state.items():
        state["temperature_c"] = round(max(22, min(40, state["temperature_c"] + random.uniform(-0.5, 0.5))), 1)
        state["rainfall_mm"] = round(max(0, state["rainfall_mm"] + random.uniform(-2, 4) * rain_factor), 2)
        state["humidity_pct"] = round(min(100, max(50, state["humidity_pct"] + random.uniform(-1, 2))), 1)
        state["wind_kmh"] = round(max(0, state["wind_kmh"] + random.uniform(-3, 3)), 1)
        state["aqi"] = max(10, min(200, state["aqi"] + random.randint(-3, 3)))
        state["flood_risk"] = _flood_risk(state["rainfall_mm"])
        state["alert"] = "HEAVY RAINFALL WARNING" if state["rainfall_mm"] > 30 else None
        events.append({**state, "timestamp": now})
    return events


class ConnectionManager:
    def __init__(self) -> None:
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self.active = [c for c in self.active if c is not ws]

    async def broadcast(self, data: Any) -> None:
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


async def _emit_loop() -> None:
    while True:
        events = _tick()
        await manager.broadcast({"type": "WEATHER_UPDATE", "zones": events})
        await asyncio.sleep(10)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    _init()
    task = asyncio.create_task(_emit_loop())
    yield
    task.cancel()


app = FastAPI(title="CityOS Weather Data Provider", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "provider": "weather"}


@app.get("/weather")
async def get_weather() -> list[dict]:
    return list(weather_state.values())


@app.websocket("/ws/weather")
async def weather_ws(ws: WebSocket) -> None:
    await manager.connect(ws)
    try:
        await ws.send_json({"type": "SNAPSHOT", "zones": list(weather_state.values())})
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)
