"""CityOS Incident Data Provider.

A software service that manufactures plausible incident events near real
Kozhikode locations and publishes them -- not a real accident/fire/flood
detection system, and not presented as one (spec section 86: never pretend
simulated data is real). Every tick has a chance of emitting a new
incident; each publish is picked up by city-core
(app/services/live_ingest.py) via the `incident.events` Redpanda/Kafka
topic and appears on the live map within seconds, the same path
data-providers/traffic and data-providers/vehicles already use.

`image_url` is a placeholder photo from picsum.photos (a public
placeholder-image service, seeded by incident id so it's stable per
incident) -- not a real photo of a real incident. It exists so the map's
inspector panel has something real to render for spec section 16's
"Evidence" field; a real deployment would replace this with an actual
citizen/officer upload through spec section 74's file-upload pipeline.
"""

import asyncio
import json
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
KAFKA_TOPIC = "incident.events"

# Real Kozhikode locations, paired with a plausible incident type for each
# -- an accident on a real road, a medical emergency near a real hospital.
TEMPLATES: list[dict[str, Any]] = [
    {
        "type": "ROAD_ACCIDENT",
        "location": "Mavoor Road",
        "lat": 11.2560,
        "lon": 75.7870,
        "descriptions": [
            "Multi-vehicle collision blocking traffic on Mavoor Road",
            "Two-wheeler skid reported on Mavoor Road near the flyover",
        ],
    },
    {
        "type": "ROAD_ACCIDENT",
        "location": "NH 66 near Ramanattukara",
        "lat": 11.2300,
        "lon": 75.8400,
        "descriptions": ["Vehicle breakdown causing tailback on NH 66 near Ramanattukara"],
    },
    {
        "type": "FLOOD",
        "location": "Beach Road",
        "lat": 11.2540,
        "lon": 75.7710,
        "descriptions": ["Waterlogging reported on Beach Road after heavy rainfall"],
    },
    {
        "type": "MEDICAL_EMERGENCY",
        "location": "near Government Medical College Kozhikode",
        "lat": 11.2495,
        "lon": 75.8575,
        "descriptions": ["Ambulance dispatch requested near Government Medical College"],
    },
    {
        "type": "MEDICAL_EMERGENCY",
        "location": "near Baby Memorial Hospital",
        "lat": 11.2598,
        "lon": 75.7920,
        "descriptions": ["Emergency medical response requested near Baby Memorial Hospital"],
    },
    {
        "type": "INFRASTRUCTURE_FAILURE",
        "location": "Chalappuram",
        "lat": 11.2560,
        "lon": 75.7830,
        "descriptions": ["Water main rupture reported in Chalappuram"],
    },
    {
        "type": "INFRASTRUCTURE_FAILURE",
        "location": "Mankavu",
        "lat": 11.2650,
        "lon": 75.7960,
        "descriptions": ["Transformer trip reported near the Mankavu grid substation"],
    },
    {
        "type": "PUBLIC_SAFETY",
        "location": "SM Street",
        "lat": 11.2506,
        "lon": 75.7817,
        "descriptions": ["Crowd control assistance requested near SM Street"],
    },
]

SEVERITY_WEIGHTS = [("LOW", 0.35), ("MEDIUM", 0.35), ("HIGH", 0.2), ("CRITICAL", 0.1)]

# Live incidents this provider has emitted, keyed by id, so /incidents can
# return a rolling snapshot the same way the other providers do.
incident_state: dict[str, dict[str, Any]] = {}


def _pick_severity() -> str:
    return random.choices(
        [s for s, _ in SEVERITY_WEIGHTS], weights=[w for _, w in SEVERITY_WEIGHTS]
    )[0]


def _generate_incident() -> dict[str, Any]:
    template = random.choice(TEMPLATES)
    incident_id = f"SYN-{uuid.uuid4().hex[:8].upper()}"
    event = {
        "incident_id": incident_id,
        "incident_type": template["type"],
        "severity": _pick_severity(),
        "description": random.choice(template["descriptions"]),
        "latitude": template["lat"] + random.uniform(-0.002, 0.002),
        "longitude": template["lon"] + random.uniform(-0.002, 0.002),
        "image_url": f"https://picsum.photos/seed/{incident_id}/600/400",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    incident_state[incident_id] = event
    # Keep the local snapshot bounded -- this provider isn't a system of
    # record (city-core is), just a rolling window for standalone testing.
    if len(incident_state) > 50:
        oldest = min(incident_state, key=lambda k: incident_state[k]["timestamp"])
        del incident_state[oldest]
    return event


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

producer: AIOKafkaProducer | None = None


async def _emit_loop() -> None:
    while True:
        # Irregular interval (20-45s) with a further chance of skipping a
        # tick entirely -- a steady drip of "incidents" every few seconds
        # would look absurd on the map; real cities don't have an accident
        # every 3 seconds.
        await asyncio.sleep(random.uniform(20, 45))
        if random.random() > 0.7:
            continue

        event = _generate_incident()
        await manager.broadcast({"type": "INCIDENT_DETECTED", "incident": event})
        if producer is not None:
            await producer.send(
                KAFKA_TOPIC, key=event["incident_id"].encode(), value=json.dumps(event).encode()
            )


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


app = FastAPI(title="CityOS Incident Data Provider", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"]
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "provider": "incidents"}


@app.get("/incidents")
async def get_incidents() -> list[dict]:
    """Rolling snapshot of incidents this provider has emitted."""
    return list(incident_state.values())


@app.websocket("/ws/incidents")
async def incidents_ws(ws: WebSocket) -> None:
    await manager.connect(ws)
    try:
        await ws.send_json({"type": "SNAPSHOT", "incidents": list(incident_state.values())})
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)
