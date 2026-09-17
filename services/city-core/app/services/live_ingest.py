"""Turns data-provider events into Road/Vehicle upserts (Phase 3 live pipeline).

Consumed by app/api/routes_live.py's Kafka consumer background task. Each
function takes an already-JSON-decoded event dict a provider published and
either updates the matching row (matched by natural key -- Road.code /
Vehicle.vehicle_id) or creates it on first sight. city-core's roads/vehicles
tables have no separate seed data today, so the provider's registry becomes
the live seed the first time this pipeline runs, the same way onboarding any
new external data source would work.

Like app/services/incidents.py, this module does not own the DB session --
callers pass one in and are responsible for committing.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import RISK_LEVELS, TRAFFIC_LEVELS, VEHICLE_TYPES, Road, Vehicle


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
