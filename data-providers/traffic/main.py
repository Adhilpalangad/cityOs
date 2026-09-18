"""CityOS Traffic Data Provider.

Continuously generates realistic traffic telemetry for the city's road network
and exposes it via HTTP + WebSocket endpoints. This is a software data service
that emulates the same interface a real ITS/traffic system would publish.

Each tick is also published to the `traffic.events` Redpanda/Kafka topic (see
`lifespan()` and `_emit_loop()` below), which is how city-core picks these
events up and turns them into live road updates -- the local WebSocket
broadcast is kept for standalone testing but is not what the rest of the
platform consumes.
"""

import asyncio
import json
import math
import os
import random
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from aiokafka import AIOKafkaProducer
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

KAFKA_BROKERS = os.environ.get("KAFKA_BROKERS", "localhost:19092")
KAFKA_TOPIC = "traffic.events"

# ---------------------------------------------------------------------------
# Synthetic road registry -- real Kozhikode road names. This provider only
# ever emits traffic counts/speeds (no geometry -- see city-core's
# app/services/live_ingest.py, which upserts a Road row by this `id` but
# can't give it a real shape from this alone), so only the names need to be
# real; the traffic numbers themselves are still synthetic.
# ---------------------------------------------------------------------------
ROADS = [
    {"id": "ROAD-1024", "name": "Mavoor Road", "capacity": 1200},
    {"id": "ROAD-1025", "name": "NH 66 (Kozhikode Bypass)", "capacity": 1800},
    {"id": "ROAD-1026", "name": "Beach Road", "capacity": 600},
    {"id": "ROAD-1027", "name": "Airport Road", "capacity": 900},
    {"id": "ROAD-1028", "name": "Mini Bypass Road", "capacity": 1000},
    {"id": "ROAD-1029", "name": "Bank Road", "capacity": 400},
]

# Live state for each road
road_state: dict[str, dict[str, Any]] = {}


def _init_road_state() -> None:
    for r in ROADS:
        road_state[r["id"]] = {
            "road_id": r["id"],
            "name": r["name"],
            "capacity": r["capacity"],
            "vehicle_count": random.randint(100, int(r["capacity"] * 0.75)),
            "average_speed_kmh": random.uniform(25, 75),
            "traffic_level": "MEDIUM",
            "risk_level": "LOW",
            "congestion_pct": 0.0,
        }


def _compute_levels(state: dict[str, Any]) -> None:
    pct = state["vehicle_count"] / state["capacity"] * 100
    state["congestion_pct"] = round(pct, 1)
    if pct < 40:
        state["traffic_level"] = "LOW"
        state["risk_level"] = "LOW"
        state["average_speed_kmh"] = round(random.uniform(60, 90), 1)
    elif pct < 65:
        state["traffic_level"] = "MEDIUM"
        state["risk_level"] = "LOW"
        state["average_speed_kmh"] = round(random.uniform(35, 60), 1)
    elif pct < 85:
        state["traffic_level"] = "HIGH"
        state["risk_level"] = "MEDIUM"
        state["average_speed_kmh"] = round(random.uniform(15, 35), 1)
    else:
        state["traffic_level"] = "CRITICAL"
        state["risk_level"] = "HIGH"
        state["average_speed_kmh"] = round(random.uniform(5, 15), 1)


def _update_traffic_state() -> list[dict[str, Any]]:
    """Simulate realistic traffic evolution each tick."""
    hour = time.localtime().tm_hour
    # Rush-hour multiplier: peaks at 8am and 5pm
    rush = 1.0 + 0.5 * (
        math.exp(-((hour - 8) ** 2) / 4) + math.exp(-((hour - 17) ** 2) / 4)
    )
    events = []
    for road_id, state in road_state.items():
        delta = random.randint(-30, 30)
        target = int(state["capacity"] * 0.55 * rush)
        state["vehicle_count"] = max(0, min(state["capacity"], state["vehicle_count"] + delta + random.randint(-5, 5)))
        _compute_levels(state)
        events.append({
            **state,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
    return events


# ---------------------------------------------------------------------------
# WebSocket manager
# ---------------------------------------------------------------------------
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

# Set by lifespan() at startup; module-level so _emit_loop() can reach it
# without threading it through every call.
producer: AIOKafkaProducer | None = None


# ---------------------------------------------------------------------------
# Background task: emit traffic updates every 3 s
# ---------------------------------------------------------------------------
async def _emit_loop() -> None:
    while True:
        events = _update_traffic_state()
        await manager.broadcast({"type": "TRAFFIC_UPDATE", "roads": events})
        if producer is not None:
            for event in events:
                await producer.send(
                    KAFKA_TOPIC, key=event["road_id"].encode(), value=json.dumps(event).encode()
                )
        await asyncio.sleep(3)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    global producer
    _init_road_state()
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BROKERS)
    try:
        await producer.start()
    except Exception:
        # Kafka isn't reachable (e.g. running this provider standalone
        # without Redpanda) -- keep serving the local WebSocket/HTTP
        # snapshot, just don't publish upstream.
        producer = None
    task = asyncio.create_task(_emit_loop())
    yield
    task.cancel()
    if producer is not None:
        await producer.stop()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="CityOS Traffic Data Provider", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "provider": "traffic"}


@app.get("/traffic/roads")
async def get_roads() -> list[dict]:
    """Snapshot of all road traffic states."""
    return list(road_state.values())


@app.get("/traffic/roads/{road_id}")
async def get_road(road_id: str) -> dict:
    state = road_state.get(road_id)
    if not state:
        return {"error": "Road not found"}
    return state


@app.websocket("/ws/traffic")
async def traffic_ws(ws: WebSocket) -> None:
    await manager.connect(ws)
    try:
        await ws.send_json({"type": "SNAPSHOT", "roads": list(road_state.values())})
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)
