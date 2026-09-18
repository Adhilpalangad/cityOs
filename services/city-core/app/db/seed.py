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

        # Roads -- real Kozhikode roads, real sourced coordinates (see
        # services/city-core/README.md's "Live data pipeline" section and
        # data-providers/traffic/main.py for where these names also appear).
        roads = [
            Road(
                id=uuid.uuid4(),
                code="ROAD-1024",
                name="Mavoor Road",
                road_type="arterial",
                status="OPEN",
                capacity=1200,
                current_vehicle_count=840,
                average_speed_kmh=42.5,
                traffic_level="HIGH",
                risk_level="MEDIUM",
                waypoints=[[11.2506, 75.7817], [11.2602, 75.7926]],
            ),
            Road(
                id=uuid.uuid4(),
                code="ROAD-1026",
                name="Beach Road",
                road_type="arterial",
                status="OPEN",
                capacity=800,
                current_vehicle_count=320,
                average_speed_kmh=58.0,
                traffic_level="LOW",
                risk_level="LOW",
                waypoints=[[11.2506, 75.7817], [11.2561, 75.7694]],
            ),
            Road(
                id=uuid.uuid4(),
                code="ROAD-1025",
                name="NH 66 (Kozhikode Bypass)",
                road_type="highway",
                status="MAINTENANCE",
                capacity=1800,
                current_vehicle_count=1100,
                average_speed_kmh=28.0,
                traffic_level="CRITICAL",
                risk_level="HIGH",
                waypoints=[[11.2646, 75.8117], [11.2190, 75.8340]],
            ),
        ]
        db.add_all(roads)

        # Hospitals -- real Kozhikode hospitals, real sourced coordinates.
        # Same codes as data-providers/hospitals/main.py's registry.
        hospitals = [
            Hospital(
                id=uuid.uuid4(),
                code="GMC-KKD",
                name="Government Medical College Kozhikode",
                latitude=11.2490,
                longitude=75.8580,
                beds_total=1850,
                beds_occupied=1480,
                icu_total=120,
                icu_occupied=96,
                emergency_capacity="HIGH",
                status="OPERATIONAL",
            ),
            Hospital(
                id=uuid.uuid4(),
                code="BMH-KKD",
                name="Baby Memorial Hospital",
                latitude=11.2602,
                longitude=75.7926,
                beds_total=500,
                beds_occupied=340,
                icu_total=55,
                icu_occupied=34,
                emergency_capacity="MEDIUM",
                status="OPERATIONAL",
            ),
            Hospital(
                id=uuid.uuid4(),
                code="MIMS-KKD",
                name="Aster MIMS Kozhikode",
                latitude=11.2459,
                longitude=75.7982,
                beds_total=670,
                beds_occupied=635,
                icu_total=70,
                icu_occupied=66,
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
                incident_type="ROAD_ACCIDENT",
                severity="CRITICAL",
                status="RESPONDING",
                description="Multi-vehicle collision blocking 2 lanes on NH 66 near Ramanattukara",
                latitude=11.2300,
                longitude=75.8400,
                department_code="TRAFFIC",
            ),
            Incident(
                id=uuid.uuid4(),
                incident_number="INC-2026-0892",
                incident_type="INFRASTRUCTURE_FAILURE",
                severity="HIGH",
                status="ASSIGNED",
                description="Transformer trip affecting Mankavu grid",
                latitude=11.2650,
                longitude=75.7950,
                department_code="ENERGY",
            ),
            Incident(
                id=uuid.uuid4(),
                incident_number="INC-2026-0893",
                incident_type="INFRASTRUCTURE_FAILURE",
                severity="MEDIUM",
                status="VERIFIED",
                description="High pressure main valve rupture reported near Chalappuram",
                latitude=11.2560,
                longitude=75.7830,
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
                latitude=11.2550,
                longitude=75.8200,
                speed_kmh=65.0,
                heading_degrees=180.0,
                position_updated_at=datetime.now(UTC),
            ),
            Vehicle(
                id=uuid.uuid4(),
                vehicle_id="BUS-402",
                vehicle_type="public_transport",
                status="ACTIVE",
                latitude=11.2506,
                longitude=75.7817,
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
                message="NH 66 near Ramanattukara experiencing heavy delay due to INC-2026-0891.",
                severity="CRITICAL",
                target_department="TRAFFIC",
                channel="IN_APP",
                is_read=False,
            ),
            Notification(
                id=uuid.uuid4(),
                title="Hospital ICU Capacity Warning",
                message="Aster MIMS Kozhikode ICU occupancy reaches 94%.",
                severity="WARNING",
                target_department="HEALTHCARE",
                channel="EMAIL",
                is_read=False,
            ),
            Notification(
                id=uuid.uuid4(),
                title="Heavy Rain Advisory",
                message="Precipitation forecast exceeded 45mm/hr in the Beypore zone.",
                severity="WARNING",
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
                zone_code="WZ-VELLAYIL",
                name="Vellayil Reservoir Zone",
                capacity_liters=5000000.0,
                consumption_lps=420.5,
                status="NORMAL",
                leak_risk="LOW",
                outages_active=0,
            ),
            WaterZone(
                id=uuid.uuid4(),
                zone_code="WZ-CHALAPPURAM",
                name="Chalappuram Distribution Zone",
                capacity_liters=3500000.0,
                consumption_lps=680.0,
                status="WARNING",
                leak_risk="HIGH",
                outages_active=1,
            ),
        ]
        db.add_all(water_zones)

        # Power Substations
        substations = [
            PowerSubstation(
                id=uuid.uuid4(),
                substation_code="SUB-MANKAVU",
                name="Mankavu Grid Substation",
                capacity_mw=250.0,
                load_mw=195.0,
                status="OPERATIONAL",
                outage_risk="MEDIUM",
            ),
            PowerSubstation(
                id=uuid.uuid4(),
                substation_code="SUB-KALLAI",
                name="Kallai Substation",
                capacity_mw=180.0,
                load_mw=172.0,
                status="HIGH_LOAD",
                outage_risk="HIGH",
            ),
        ]
        db.add_all(substations)

        # Environment
        env_readings = [
            EnvironmentReading(
                id=uuid.uuid4(),
                zone_code="ZONE-BEYPORE",
                temperature_c=28.5,
                rainfall_mm=12.4,
                humidity_pct=72.0,
                aqi=45,
                flood_risk="LOW",
            ),
            EnvironmentReading(
                id=uuid.uuid4(),
                zone_code="ZONE-WESTHILL",
                temperature_c=31.0,
                rainfall_mm=48.0,
                humidity_pct=88.0,
                aqi=82,
                flood_risk="HIGH",
            ),
        ]
        db.add_all(env_readings)

        # Complaints
        complaints = [
            CitizenComplaint(
                id=uuid.uuid4(),
                complaint_number="CMP-2026-0041",
                title="Pothole near Mananchira Bus Station",
                description="Large pothole causing vehicle slowdowns and safety hazards.",
                category="ROADS",
                status="SUBMITTED",
                reporter_email="citizen1@example.com",
                department_code="INFRASTRUCTURE",
            ),
            CitizenComplaint(
                id=uuid.uuid4(),
                complaint_number="CMP-2026-0042",
                title="Streetlight failure on Bank Road",
                description="Multiple streetlights dark creating unsafe night crossing.",
                category="LIGHTING",
                status="ASSIGNED",
                reporter_email="citizen2@example.com",
                department_code="ENERGY",
            ),
        ]
        db.add_all(complaints)

        # Projects & Assets
        assets = [
            InfrastructureAsset(
                id=uuid.uuid4(),
                asset_code="AST-BR-01",
                name="Kallai River Bridge",
                asset_type="Bridge",
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
                project_code="PRJ-BYPASS-04",
                name="Mini Bypass Road Widening",
                department_code="INFRASTRUCTURE",
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
                title="Inspect valve leak near Chalappuram",
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
