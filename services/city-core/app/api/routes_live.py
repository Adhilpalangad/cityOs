"""Live WebSocket feed + the Kafka consumer that feeds it (Phase 3).

Bridges the three data providers (data-providers/traffic, data-providers/
vehicles, data-providers/incidents) to the rest of the platform: their
events land on the `traffic.events` / `vehicle.events` / `incident.events`
Redpanda topics, get applied to Road/Vehicle/Incident rows by
`app/services/live_ingest.py`, and are rebroadcast here over `/ws/live` so
the browser sees updates without polling. api-gateway relays this endpoint
through to the browser (see services/api-gateway/app/api/ws_proxy.py)
rather than exposing city-core directly.
"""

import json
from typing import Any

import structlog
from aiokafka import AIOKafkaConsumer
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.core.config import get_settings
from app.core.security import TokenError, decode_access_token
from app.db.base import SessionLocal
from app.db.models import Incident, Road, Vehicle
from app.schemas.incidents import IncidentRead
from app.schemas.roads import RoadRead
from app.schemas.vehicles import VehicleRead
from app.services.live_ingest import apply_incident_event, apply_traffic_event, apply_vehicle_event
from app.services.notifications import notify

router = APIRouter()
logger = structlog.get_logger()

_TOPICS = ("traffic.events", "vehicle.events", "incident.events")


def _road_to_read(road: Road) -> RoadRead:
    return RoadRead(
        id=str(road.id),
        code=road.code,
        name=road.name,
        road_type=road.road_type,
        status=road.status,
        capacity=road.capacity,
        current_vehicle_count=road.current_vehicle_count,
        average_speed_kmh=road.average_speed_kmh,
        traffic_level=road.traffic_level,
        risk_level=road.risk_level,
        waypoints=[tuple(point) for point in road.waypoints],
        created_at=road.created_at,
        updated_at=road.updated_at,
    )


def _vehicle_to_read(vehicle: Vehicle) -> VehicleRead:
    return VehicleRead(
        id=str(vehicle.id),
        vehicle_id=vehicle.vehicle_id,
        vehicle_type=vehicle.vehicle_type,
        status=vehicle.status,
        latitude=vehicle.latitude,
        longitude=vehicle.longitude,
        speed_kmh=vehicle.speed_kmh,
        heading_degrees=vehicle.heading_degrees,
        position_updated_at=vehicle.position_updated_at,
        created_at=vehicle.created_at,
        updated_at=vehicle.updated_at,
    )


def _incident_to_read(incident: Incident) -> IncidentRead:
    return IncidentRead(
        id=str(incident.id),
        incident_number=incident.incident_number,
        incident_type=incident.incident_type,
        severity=incident.severity,
        status=incident.status,
        description=incident.description,
        latitude=incident.latitude,
        longitude=incident.longitude,
        road_id=str(incident.road_id) if incident.road_id else None,
        reporter=incident.reporter,
        department_code=incident.department_code,
        assigned_to=incident.assigned_to,
        response_time_seconds=incident.response_time_seconds,
        resolved_at=incident.resolved_at,
        image_url=incident.image_url,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
    )


class ConnectionManager:
    def __init__(self) -> None:
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self.active = [c for c in self.active if c is not ws]

    async def broadcast(self, data: dict[str, Any]) -> None:
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


@router.websocket("/ws/live")
async def live_feed(ws: WebSocket, token: str | None = None) -> None:
    """Authenticated live feed of Road/Vehicle updates.

    Browsers can't set an `Authorization` header on a WebSocket handshake, so
    the access token travels as a query parameter instead -- the same JWT the
    HTTP API accepts via `Depends(get_current_user)` in app/api/deps.py.
    """
    settings = get_settings()
    if token is None:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    try:
        decode_access_token(settings, token)
    except TokenError:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(ws)
    try:
        while True:
            # This endpoint only pushes; block on a client message so the
            # connection's lifetime is governed by disconnect detection.
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)


async def _handle_message(topic: str, payload: bytes) -> None:
    event = json.loads(payload)
    async with SessionLocal() as db:
        if topic == "traffic.events":
            road = await apply_traffic_event(db, event)
            await db.commit()
            await manager.broadcast(
                {"type": "ROAD_UPDATE", "road": _road_to_read(road).model_dump(mode="json")}
            )
        elif topic == "vehicle.events":
            vehicle = await apply_vehicle_event(db, event)
            await db.commit()
            await manager.broadcast(
                {
                    "type": "VEHICLE_UPDATE",
                    "vehicle": _vehicle_to_read(vehicle).model_dump(mode="json"),
                }
            )
        elif topic == "incident.events":
            incident = await apply_incident_event(db, event)
            # Spec section 48's trigger rule applies here too, not just to
            # incidents created through the REST API (routes_incidents.py).
            if incident.severity == "CRITICAL":
                notify(
                    db,
                    title=f"Critical incident: {incident.incident_number}",
                    message=incident.description or f"{incident.incident_type} detected.",
                    severity="CRITICAL",
                    target_department=incident.department_code or "EMERGENCY",
                )
            await db.commit()
            await manager.broadcast(
                {
                    "type": "INCIDENT_UPDATE",
                    "incident": _incident_to_read(incident).model_dump(mode="json"),
                }
            )


async def run_consumer() -> None:
    """The Kafka consumer loop -- started as a background task from main.py's
    lifespan. Runs until cancelled; swallows a missing/unreachable broker
    into a logged warning rather than crashing the service, since city-core's
    REST API should keep working even if Redpanda is down.
    """
    settings = get_settings()
    consumer = AIOKafkaConsumer(
        *_TOPICS,
        bootstrap_servers=settings.kafka_brokers,
        group_id="city-core-live-ingest",
        auto_offset_reset="latest",
    )
    try:
        await consumer.start()
    except Exception as exc:
        logger.warning("live_ingest_kafka_unavailable", error=str(exc))
        return
    try:
        async for message in consumer:
            try:
                await _handle_message(message.topic, message.value)
            except Exception:
                logger.exception("live_ingest_event_failed", topic=message.topic)
    finally:
        await consumer.stop()
