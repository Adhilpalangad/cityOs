"""CityOS Vehicle Data Provider.

Continuously generates realistic vehicle GPS telemetry for buses, ambulances,
and fleet vehicles. Exposes HTTP snapshots and WebSocket streaming.

Each tick is also published to the `vehicle.events` Redpanda/Kafka topic (see
`lifespan()` and `_emit_loop()` below), which is how city-core picks these
events up and turns them into live vehicle updates -- the local WebSocket
broadcast is kept for standalone testing but is not what the rest of the
platform consumes.
"""

import asyncio
import json
import math
import os
import random
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from aiokafka import AIOKafkaProducer
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

KAFKA_BROKERS = os.environ.get("KAFKA_BROKERS", "localhost:19092")
KAFKA_TOPIC = "vehicle.events"

# ---------------------------------------------------------------------------
# Vehicle registry -- jittered around real Kozhikode locations: buses near
# the city centre/Mananchira, ambulances near the Medical College/Baby
# Memorial Hospital area, fleet vehicles out toward Thondayad Junction.
# ---------------------------------------------------------------------------
VEHICLES: list[dict[str, Any]] = [
    {"vehicle_id": f"BUS-{101 + i}", "type": "public_transport",
     "lat": 11.2506 + random.uniform(-0.02, 0.02),
     "lon": 75.7817 + random.uniform(-0.02, 0.02),
     "heading": random.uniform(0, 360), "speed": random.uniform(20, 50)}
    for i in range(12)
] + [
    {"vehicle_id": f"AMB-{17 + i}", "type": "ambulance",
     "lat": 11.2550 + random.uniform(-0.015, 0.015),
     "lon": 75.8200 + random.uniform(-0.02, 0.02),
     "heading": random.uniform(0, 360), "speed": random.uniform(0, 80)}
    for i in range(6)
] + [
    {"vehicle_id": f"FLT-{201 + i}", "type": "fleet",
     "lat": 11.2600 + random.uniform(-0.015, 0.015),
     "lon": 75.8000 + random.uniform(-0.015, 0.015),
     "heading": random.uniform(0, 360), "speed": random.uniform(10, 40)}
    for i in range(8)
]

vehicle_state: dict[str, dict[str, Any]] = {
    v["vehicle_id"]: dict(v) for v in VEHICLES
}


def _move_vehicle(v: dict[str, Any]) -> None:
    """Simulate realistic GPS movement along a heading."""
    speed = v["speed"]
    heading_rad = math.radians(v["heading"])
    # Earth radius in km
    R = 6371.0
    dist_km = speed / 3600 * 3  # 3 second tick
    delta_lat = (dist_km / R) * math.cos(heading_rad) * (180 / math.pi)
    delta_lon = (dist_km / R) * math.sin(heading_rad) * (180 / math.pi) / math.cos(math.radians(v["lat"]))
    v["lat"] = round(v["lat"] + delta_lat, 6)
    v["lon"] = round(v["lon"] + delta_lon, 6)
    # Slight heading drift & speed fluctuation
    v["heading"] = (v["heading"] + random.uniform(-8, 8)) % 360
    v["speed"] = max(0, v["speed"] + random.uniform(-5, 5))
    # Clamp to city bounds
    # Roughly Kozhikode city proper -- centre out to Thondayad/Medical College.
    v["lat"] = max(11.15, min(11.30, v["lat"]))
    v["lon"] = max(75.75, min(75.90, v["lon"]))


def _get_events() -> list[dict[str, Any]]:
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    events = []
    for vid, state in vehicle_state.items():
        _move_vehicle(state)
        events.append({
            "vehicle_id": vid,
            "type": state["type"],
            "latitude": state["lat"],
            "longitude": state["lon"],
            "speed": round(state["speed"], 1),
            "heading": round(state["heading"], 1),
            "timestamp": now,
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


async def _emit_loop() -> None:
    while True:
        events = _get_events()
        await manager.broadcast({"type": "VEHICLE_POSITIONS", "vehicles": events})
        if producer is not None:
            for event in events:
                await producer.send(
                    KAFKA_TOPIC, key=event["vehicle_id"].encode(), value=json.dumps(event).encode()
                )
        await asyncio.sleep(3)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    global producer
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
app = FastAPI(title="CityOS Vehicle Data Provider", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"]
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "provider": "vehicles"}


@app.get("/vehicles")
async def get_vehicles() -> list[dict]:
    return _get_events()


@app.websocket("/ws/vehicles")
async def vehicles_ws(ws: WebSocket) -> None:
    await manager.connect(ws)
    try:
        await ws.send_json({"type": "SNAPSHOT", "vehicles": _get_events()})
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)
