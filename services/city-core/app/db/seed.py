"""Seed script for city-core database.

Populates initial sample data for roads, hospitals, vehicles, incidents, transit,
water zones, power substations, environment readings, infrastructure, projects,
complaints, workflow tasks, audit logs, notifications, and knowledge base documents.
"""

import asyncio
import sys
import uuid
from datetime import UTC, datetime

from sqlalchemy import select

from app.db.base import SessionLocal
from app.db.models import (
    AuditLog,
    BusStop,
    CitizenComplaint,
    CityProject,
    EnvironmentReading,
    Hospital,
    Incident,
    InfrastructureAsset,
    KnowledgeDocument,
    Notification,
    PowerSubstation,
    Road,
    SimulationScenario,
    TransitRoute,
    Vehicle,
    WaterZone,
    WorkflowTask,
)


async def seed() -> None:
    async with SessionLocal() as db:
        # 1. Check if seeded
        existing_roads = await db.scalar(select(Road))
        if existing_roads:
            print("Database already seeded. Skipping.")
            return

        print("Seeding city-core database...")

        # Roads
        roads = [
            Road(
                id=uuid.uuid4(),
                code="ROAD-101",
                name="Grand Coastal Arterial",
                road_type="expressway",
                status="OPEN",
                capacity=1200,
                current_vehicle_count=840,
                average_speed_kmh=42.5,
                traffic_level="HIGH",
                risk_level="MEDIUM",
                waypoints=[[12.9716, 77.5946], [12.9750, 77.5990]],
            ),
            Road(
                id=uuid.uuid4(),
                code="ROAD-102",
                name="Metro Central Boulevard",
                road_type="arterial",
                status="OPEN",
                capacity=800,
                current_vehicle_count=320,
                average_speed_kmh=58.0,
                traffic_level="LOW",
                risk_level="LOW",
                waypoints=[[12.9600, 77.5800], [12.9650, 77.5850]],
            ),
            Road(
                id=uuid.uuid4(),
                code="ROAD-103",
                name="Tech Corridor Bypass",
                road_type="highway",
                status="MAINTENANCE",
                capacity=1500,
                current_vehicle_count=1100,
                average_speed_kmh=28.0,
                traffic_level="CRITICAL",
                risk_level="HIGH",
                waypoints=[[12.9800, 77.6000], [12.9900, 77.6100]],
            ),
        ]
        db.add_all(roads)

        # Hospitals
        hospitals = [
            Hospital(
                id=uuid.uuid4(),
                code="HOSP-01",
                name="Central Metropolitan Hospital",
                latitude=12.9716,
                longitude=77.5946,
                beds_total=450,
                beds_occupied=380,
                icu_total=60,
                icu_occupied=52,
                emergency_capacity="HIGH",
                status="OPERATIONAL",
            ),
            Hospital(
                id=uuid.uuid4(),
                code="HOSP-02",
                name="Eastside Trauma & General",
                latitude=12.9820,
                longitude=77.6120,
                beds_total=280,
                beds_occupied=190,
                icu_total=35,
                icu_occupied=22,
                emergency_capacity="MEDIUM",
                status="OPERATIONAL",
            ),
            Hospital(
                id=uuid.uuid4(),
                code="HOSP-03",
                name="St. Jude Emergency Center",
                latitude=12.9550,
                longitude=77.5750,
                beds_total=150,
                beds_occupied=142,
                icu_total=20,
                icu_occupied=19,
                emergency_capacity="CRITICAL",
                status="LIMITED",
            ),
        ]
        db.add_all(hospitals)

        # Incidents
        incidents = [
            Incident(
                id=uuid.uuid4(),
                incident_number="INC-2026-0891",
                incident_type="TRAFFIC_ACCIDENT",
                severity="CRITICAL",
                status="DISPATCHED",
                description="Multi-vehicle collision blocking 2 lanes on Tech Corridor Bypass",
                latitude=12.9850,
                longitude=77.6050,
                department_code="TRAFFIC",
            ),
            Incident(
                id=uuid.uuid4(),
                incident_number="INC-2026-0892",
                incident_type="POWER_OUTAGE",
                severity="HIGH",
                status="IN_PROGRESS",
                description="Transformer trip affecting Metro Central North district",
                latitude=12.9620,
                longitude=77.5830,
                department_code="ENERGY",
            ),
            Incident(
                id=uuid.uuid4(),
                incident_number="INC-2026-0893",
                incident_type="WATER_LEAK",
                severity="MEDIUM",
                status="REPORTED",
                description="High pressure main valve rupture reported by citizen",
                latitude=12.9700,
                longitude=77.5900,
                department_code="WATER",
            ),
        ]
        db.add_all(incidents)

        # Vehicles
        vehicles = [
            Vehicle(
                id=uuid.uuid4(),
                vehicle_id="AMB-101",
                vehicle_type="ambulance",
                status="ACTIVE",
                latitude=12.9720,
                longitude=77.5950,
                speed_kmh=65.0,
                heading_degrees=180.0,
                position_updated_at=datetime.now(UTC),
            ),
            Vehicle(
                id=uuid.uuid4(),
                vehicle_id="BUS-402",
                vehicle_type="public_transport",
                status="ACTIVE",
                latitude=12.9610,
                longitude=77.5810,
                speed_kmh=35.0,
                heading_degrees=90.0,
                position_updated_at=datetime.now(UTC),
            ),
        ]
        db.add_all(vehicles)

        # Notifications
        notifications = [
            Notification(
                id=uuid.uuid4(),
                title="Critical Traffic Alert",
                message="Tech Corridor Bypass experiencing heavy delay due to INC-2026-0891.",
                severity="CRITICAL",
                target_department="TRAFFIC",
                channel="DASHBOARD",
                is_read=False,
            ),
            Notification(
                id=uuid.uuid4(),
                title="Hospital ICU Capacity Warning",
                message="St. Jude Emergency Center ICU occupancy reaches 95%.",
                severity="HIGH",
                target_department="HEALTHCARE",
                channel="EMAIL",
                is_read=False,
            ),
            Notification(
                id=uuid.uuid4(),
                title="Heavy Rain Advisory",
                message="Precipitation forecast exceeded 45mm/hr in North Zone.",
                severity="MEDIUM",
                target_department="ENVIRONMENT",
                channel="SMS",
                is_read=True,
            ),
        ]
        db.add_all(notifications)

        # Water Zones
        water_zones = [
            WaterZone(
                id=uuid.uuid4(),
                zone_code="WZ-NORTH",
                name="North District Water Supply",
                capacity_liters=5000000.0,
                consumption_lps=420.5,
                status="OPERATIONAL",
                leak_risk="LOW",
                outages_active=0,
            ),
            WaterZone(
                id=uuid.uuid4(),
                zone_code="WZ-CENTRAL",
                name="Central Commercial Grid",
                capacity_liters=3500000.0,
                consumption_lps=680.0,
                status="LIMITED",
                leak_risk="HIGH",
                outages_active=1,
            ),
        ]
        db.add_all(water_zones)

        # Power Substations
        substations = [
            PowerSubstation(
                id=uuid.uuid4(),
                substation_code="SUB-GRID-01",
                name="Grand Coastal Substation Alpha",
                capacity_mw=250.0,
                load_mw=195.0,
                status="OPERATIONAL",
                outage_risk="MEDIUM",
            ),
            PowerSubstation(
                id=uuid.uuid4(),
                substation_code="SUB-GRID-02",
                name="Metro Central Substation Beta",
                capacity_mw=180.0,
                load_mw=172.0,
                status="LIMITED",
                outage_risk="HIGH",
            ),
        ]
        db.add_all(substations)

        # Environment
        env_readings = [
            EnvironmentReading(
                id=uuid.uuid4(),
                zone_code="ZONE-NORTH",
                temperature_c=28.5,
                rainfall_mm=12.4,
                humidity_pct=72.0,
                aqi=45,
                flood_risk="LOW",
            ),
            EnvironmentReading(
                id=uuid.uuid4(),
                zone_code="ZONE-SOUTH",
                temperature_c=31.0,
                rainfall_mm=48.0,
                humidity_pct=88.0,
                aqi=82,
                flood_risk="MODERATE",
            ),
        ]
        db.add_all(env_readings)

        # Complaints
        complaints = [
            CitizenComplaint(
                id=uuid.uuid4(),
                complaint_number="CMP-2026-0041",
                title="Pothole near Central Market Bus Station",
                description="Large pothole causing vehicle slowdowns and safety hazards.",
                category="ROADS",
                status="OPEN",
                reporter_email="citizen1@example.com",
                department_code="INFRASTRUCTURE",
            ),
            CitizenComplaint(
                id=uuid.uuid4(),
                complaint_number="CMP-2026-0042",
                title="Streetlight failure on 4th Main",
                description="Multiple streetlights dark creating unsafe night crossing.",
                category="LIGHTING",
                status="IN_PROGRESS",
                reporter_email="citizen2@example.com",
                department_code="ENERGY",
            ),
        ]
        db.add_all(complaints)

        # Projects & Assets
        assets = [
            InfrastructureAsset(
                id=uuid.uuid4(),
                asset_code="AST-BRG-01",
                name="Harbor Flyover Bridge Span",
                asset_type="BRIDGE",
                department_code="INFRASTRUCTURE",
                condition="GOOD",
                risk_level="LOW",
                estimated_cost=4500000.0,
            ),
        ]
        db.add_all(assets)

        projects = [
            CityProject(
                id=uuid.uuid4(),
                project_code="PRJ-METRO-04",
                name="Metro Line 4 Underground Extension",
                department_code="TRANSIT",
                budget=125000000.0,
                spent=84000000.0,
                status="IN_PROGRESS",
                completion_percentage=67.2,
            ),
        ]
        db.add_all(projects)

        # Workflows
        tasks = [
            WorkflowTask(
                id=uuid.uuid4(),
                task_number="TSK-2026-012",
                title="Inspect valve leak at Central Market",
                department_code="WATER",
                assigned_to="Engineer R. Sharma",
                priority="HIGH",
                status="IN_PROGRESS",
            ),
        ]
        db.add_all(tasks)

        # Knowledge
        docs = [
            KnowledgeDocument(
                id=uuid.uuid4(),
                doc_code="DOC-EMG-001",
                title="City Emergency Response & Evacuation Protocol v4",
                category="EMERGENCY",
                content="Standard operating procedure for Tier-1 emergency evacuations...",
                tags=["emergency", "evacuation", "protocol"],
            ),
        ]
        db.add_all(docs)

        await db.commit()
        print("Successfully seeded city-core database!")


if __name__ == "__main__":
    sys.exit(asyncio.run(seed()))
