"""Tests for app/services/live_ingest.py's provider-event upserts (Phase 3).

Uses the `db` fixture directly (see tests/conftest.py) rather than the HTTP
`client` fixture -- these functions are called from a Kafka consumer, not a
route, so there's no HTTP layer to go through.
"""

from sqlalchemy import select

from app.db.models import Incident, Road, Vehicle
from app.services.live_ingest import apply_incident_event, apply_traffic_event, apply_vehicle_event

TRAFFIC_EVENT = {
    "road_id": "ROAD-1024",
    "name": "Metro Arterial North",
    "capacity": 1200,
    "vehicle_count": 640,
    "average_speed_kmh": 42.5,
    "traffic_level": "HIGH",
    "risk_level": "MEDIUM",
    "congestion_pct": 53.3,
    "timestamp": "2026-09-17T11:40:00Z",
}

VEHICLE_EVENT = {
    "vehicle_id": "BUS-101",
    "type": "public_transport",
    "latitude": 9.9816,
    "longitude": 76.2999,
    "speed": 34.0,
    "heading": 142.0,
    "timestamp": "2026-09-17T11:40:00Z",
}


async def test_apply_traffic_event_creates_road_on_first_sight(db) -> None:
    road = await apply_traffic_event(db, TRAFFIC_EVENT)
    await db.commit()

    assert road.code == "ROAD-1024"
    assert road.name == "Metro Arterial North"
    assert road.current_vehicle_count == 640
    assert road.traffic_level == "HIGH"

    stored = await db.scalar(select(Road).where(Road.code == "ROAD-1024"))
    assert stored is not None
    assert stored.risk_level == "MEDIUM"


async def test_apply_traffic_event_updates_existing_road_without_duplicating(db) -> None:
    await apply_traffic_event(db, TRAFFIC_EVENT)
    await db.commit()

    second = {**TRAFFIC_EVENT, "vehicle_count": 950, "traffic_level": "CRITICAL"}
    road = await apply_traffic_event(db, second)
    await db.commit()

    all_roads = (await db.scalars(select(Road))).all()
    assert len(all_roads) == 1
    assert road.current_vehicle_count == 950
    assert road.traffic_level == "CRITICAL"


async def test_apply_traffic_event_ignores_unrecognized_level_values(db) -> None:
    bad = {**TRAFFIC_EVENT, "traffic_level": "NONSENSE"}
    road = await apply_traffic_event(db, bad)
    await db.commit()
    assert road.traffic_level == "LOW"  # ORM default; the bad value is dropped, not stored


async def test_apply_vehicle_event_creates_vehicle_on_first_sight(db) -> None:
    vehicle = await apply_vehicle_event(db, VEHICLE_EVENT)
    await db.commit()

    assert vehicle.vehicle_id == "BUS-101"
    assert vehicle.vehicle_type == "public_transport"
    assert vehicle.latitude == 9.9816
    assert vehicle.position_updated_at is not None

    stored = await db.scalar(select(Vehicle).where(Vehicle.vehicle_id == "BUS-101"))
    assert stored is not None


async def test_apply_vehicle_event_updates_existing_vehicle_without_duplicating(db) -> None:
    await apply_vehicle_event(db, VEHICLE_EVENT)
    await db.commit()

    moved = {**VEHICLE_EVENT, "latitude": 9.99, "longitude": 76.31, "speed": 50.0}
    vehicle = await apply_vehicle_event(db, moved)
    await db.commit()

    all_vehicles = (await db.scalars(select(Vehicle))).all()
    assert len(all_vehicles) == 1
    assert vehicle.latitude == 9.99
    assert vehicle.speed_kmh == 50.0


async def test_apply_vehicle_event_falls_back_to_fleet_for_unknown_type(db) -> None:
    unknown_type = {**VEHICLE_EVENT, "vehicle_id": "X-1", "type": "spaceship"}
    vehicle = await apply_vehicle_event(db, unknown_type)
    await db.commit()
    assert vehicle.vehicle_type == "fleet"


INCIDENT_EVENT = {
    "incident_id": "SYN-ABCD1234",
    "incident_type": "ROAD_ACCIDENT",
    "severity": "HIGH",
    "description": "Multi-vehicle collision blocking traffic on Mavoor Road",
    "latitude": 11.256,
    "longitude": 75.787,
    "image_url": "https://picsum.photos/seed/SYN-ABCD1234/600/400",
    "timestamp": "2026-09-17T11:40:00Z",
}


async def test_apply_incident_event_creates_a_real_incident(db) -> None:
    incident = await apply_incident_event(db, INCIDENT_EVENT)
    await db.commit()

    assert incident.incident_number.startswith("INC-")
    assert incident.incident_type == "ROAD_ACCIDENT"
    assert incident.severity == "HIGH"
    assert incident.status == "DETECTED"
    assert incident.image_url == INCIDENT_EVENT["image_url"]
    assert incident.latitude == 11.256

    stored = await db.scalar(
        select(Incident).where(Incident.incident_number == incident.incident_number)
    )
    assert stored is not None


async def test_apply_incident_event_always_creates_a_new_row(db) -> None:
    # Unlike roads/vehicles, two incident events never collapse into one
    # row -- each is a distinct detected event, even from the same provider
    # "incident_id" (which city-core doesn't use as a natural key at all).
    await apply_incident_event(db, INCIDENT_EVENT)
    await apply_incident_event(db, INCIDENT_EVENT)
    await db.commit()

    all_incidents = (await db.scalars(select(Incident))).all()
    assert len(all_incidents) == 2


async def test_apply_incident_event_falls_back_on_unrecognized_type_and_severity(db) -> None:
    bad = {**INCIDENT_EVENT, "incident_type": "ALIEN_INVASION", "severity": "APOCALYPTIC"}
    incident = await apply_incident_event(db, bad)
    await db.commit()
    assert incident.incident_type == "PUBLIC_SAFETY"
    assert incident.severity == "MEDIUM"
