"""CityOS Hospital Data Provider.

Simulates real-time hospital capacity telemetry — bed occupancy, ICU load,
emergency department status, and ambulance availability.
"""

import asyncio
import random
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Real Kozhikode hospitals, real coordinates (Wikipedia / OSM-sourced;
# Government Medical College's is an estimate -- "~8km east of the city
# centre" per its own published description, not a surveyed pin). Bed/ICU
# counts are approximate publicly reported figures, not live data.
HOSPITALS: list[dict[str, Any]] = [
    {
        "code": "GMC-KKD", "name": "Government Medical College Kozhikode",
        "beds_total": 1850, "icu_total": 120, "lat": 11.2490, "lon": 75.8580,
    },
    {
        "code": "BMH-KKD", "name": "Baby Memorial Hospital",
        "beds_total": 500, "icu_total": 55, "lat": 11.2602, "lon": 75.7926,
    },
    {
        "code": "MIMS-KKD", "name": "Aster MIMS Kozhikode",
        "beds_total": 670, "icu_total": 70, "lat": 11.2459, "lon": 75.7982,
    },
]

hospital_state: dict[str, dict[str, Any]] = {}


def _init_hospitals() -> None:
    for h in HOSPITALS:
        hospital_state[h["code"]] = {
            **h,
            "beds_occupied": random.randint(int(h["beds_total"] * 0.60), int(h["beds_total"] * 0.85)),
            "icu_occupied": random.randint(int(h["icu_total"] * 0.55), int(h["icu_total"] * 0.90)),
            "ambulances_available": random.randint(2, 6),
            "emergency_capacity": "MEDIUM",
            "status": "OPERATIONAL",
        }
    _update_levels()


def _update_levels() -> None:
    for state in hospital_state.values():
        bed_pct = state["beds_occupied"] / state["beds_total"]
        icu_pct = state["icu_occupied"] / state["icu_total"]
        if bed_pct < 0.70 and icu_pct < 0.75:
            state["emergency_capacity"] = "LOW"
        elif bed_pct < 0.85 and icu_pct < 0.90:
            state["emergency_capacity"] = "MEDIUM"
        elif bed_pct < 0.95:
            state["emergency_capacity"] = "HIGH"
            state["status"] = "LIMITED"
        else:
            state["emergency_capacity"] = "CRITICAL"
            state["status"] = "LIMITED"


def _tick() -> list[dict[str, Any]]:
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    events = []
    for code, state in hospital_state.items():
        state["beds_occupied"] = max(0, min(state["beds_total"], state["beds_occupied"] + random.randint(-3, 5)))
        state["icu_occupied"] = max(0, min(state["icu_total"], state["icu_occupied"] + random.randint(-1, 2)))
        state["ambulances_available"] = max(0, min(8, state["ambulances_available"] + random.randint(-1, 1)))
        _update_levels()
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
        await manager.broadcast({"type": "HOSPITAL_UPDATE", "hospitals": events})
        await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    _init_hospitals()
    task = asyncio.create_task(_emit_loop())
    yield
    task.cancel()


app = FastAPI(title="CityOS Hospital Data Provider", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "provider": "hospitals"}


@app.get("/hospitals")
async def get_hospitals() -> list[dict]:
    return list(hospital_state.values())


@app.websocket("/ws/hospitals")
async def hospitals_ws(ws: WebSocket) -> None:
    await manager.connect(ws)
    try:
        await ws.send_json({"type": "SNAPSHOT", "hospitals": list(hospital_state.values())})
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)
