"""Turns data-provider events into Road/Vehicle/Incident writes (Phase 3
live pipeline).

Consumed by app/api/routes_live.py's Kafka consumer background task. Each
function takes an already-JSON-decoded event dict a provider published.
Road/Vehicle events upsert (matched by natural key -- Road.code /
Vehicle.vehicle_id) or create on first sight; city-core's roads/vehicles
tables have no separate seed data today, so the provider's registry becomes
the live seed the first time this pipeline runs. Incident events are always
new rows -- each one from data-providers/incidents represents a distinct
detected event, not an update to an existing one.

Like app/services/incidents.py, this module does not own the DB session --
callers pass one in and are responsible for committing.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    INCIDENT_SEVERITIES,
    INCIDENT_TYPES,
    RISK_LEVELS,
    TRAFFIC_LEVELS,
    VEHICLE_TYPES,
    Incident,
    Road,
    Vehicle,
)
from app.services.incidents import generate_incident_number


async def apply_traffic_event(db: AsyncSession, event: dict[str, Any]) -> Road:
    """Upsert a Road row from a `traffic.events` message.

    Expected shape (data-providers/traffic/main.py's `_update_traffic_state`):
    road_id, name, capacity, vehicle_count, average_speed_kmh, traffic_level,
    risk_level, congestion_pct, timestamp.
    """
    code = event["road_id"]
    road = await db.scalar(select(Road).where(Road.code == code))
    if road is None:
        road = Road(code=code, name=event.get("name", code), road_type="arterial", status="OPEN")
        db.add(road)

    road.name = event.get("name", road.name)
    road.capacity = event.get("capacity", road.capacity)
    road.current_vehicle_count = event.get("vehicle_count", road.current_vehicle_count)
    road.average_speed_kmh = event.get("average_speed_kmh", road.average_speed_kmh)
    traffic_level = event.get("traffic_level")
    if traffic_level in TRAFFIC_LEVELS:
        road.traffic_level = traffic_level
    risk_level = event.get("risk_level")
    if risk_level in RISK_LEVELS:
        road.risk_level = risk_level
    return road


async def apply_vehicle_event(db: AsyncSession, event: dict[str, Any]) -> Vehicle:
    """Upsert a Vehicle row from a `vehicle.events` message.

    Expected shape (data-providers/vehicles/main.py's `_get_events`):
    vehicle_id, type, latitude, longitude, speed, heading, timestamp.
    """
    vehicle_id = event["vehicle_id"]
    vehicle = await db.scalar(select(Vehicle).where(Vehicle.vehicle_id == vehicle_id))
    if vehicle is None:
        vehicle_type = event.get("type") if event.get("type") in VEHICLE_TYPES else "fleet"
        vehicle = Vehicle(vehicle_id=vehicle_id, vehicle_type=vehicle_type, status="ACTIVE")
        db.add(vehicle)

    vehicle.latitude = event.get("latitude", vehicle.latitude)
    vehicle.longitude = event.get("longitude", vehicle.longitude)
    vehicle.speed_kmh = event.get("speed", vehicle.speed_kmh)
    vehicle.heading_degrees = event.get("heading", vehicle.heading_degrees)
    vehicle.position_updated_at = datetime.now(UTC)
    return vehicle


async def apply_incident_event(db: AsyncSession, event: dict[str, Any]) -> Incident:
    """Create an Incident row from an `incident.events` message.

    Expected shape (data-providers/incidents/main.py's `_generate_incident`):
    incident_id, incident_type, severity, description, latitude, longitude,
    image_url, timestamp. Always creates -- each message is a distinct
    detected event, not an update to a prior one (matching how a real
    accident-detection feed would work: every message is a new incident).
    """
    incident_type = event.get("incident_type")
    if incident_type not in INCIDENT_TYPES:
        incident_type = "PUBLIC_SAFETY"
    severity = event.get("severity")
    if severity not in INCIDENT_SEVERITIES:
        severity = "MEDIUM"

    incident = Incident(
        incident_number=generate_incident_number(),
        incident_type=incident_type,
        severity=severity,
        description=event.get("description"),
        latitude=event.get("latitude"),
        longitude=event.get("longitude"),
        image_url=event.get("image_url"),
        department_code="EMERGENCY",
        status="DETECTED",
    )
    db.add(incident)
    return incident
