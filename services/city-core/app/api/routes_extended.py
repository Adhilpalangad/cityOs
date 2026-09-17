import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_permission
from app.db.models import (
    AuditLog,
    BusStop,
    CitizenComplaint,
    EnvironmentReading,
    Hospital,
    Incident,
    KnowledgeDocument,
    PowerSubstation,
    Road,
    SimulationScenario,
    TransitRoute,
    Vehicle,
    WaterZone,
)
from app.schemas.domains import (
    AIAnalysisRequest,
    AIAnalysisResponse,
    AuditLogRead,
    BusStopRead,
    CitizenComplaintCreate,
    CitizenComplaintRead,
    EnvironmentReadingRead,
    KnowledgeDocumentRead,
    PowerSubstationRead,
    SimulationScenarioCreate,
    SimulationScenarioRead,
    TransitRouteRead,
    WaterZoneRead,
)

router = APIRouter()


# -----------------------------------------------------------------------------
# Transit
# -----------------------------------------------------------------------------
@router.get(
    "/api/v1/routes",
    response_model=list[TransitRouteRead],
    dependencies=[Depends(require_permission("transit.read"))],
)
async def list_transit_routes(db: AsyncSession = Depends(get_db)):
    stmt = select(TransitRoute).order_by(TransitRoute.route_number.asc())
    routes = (await db.scalars(stmt)).all()
    if not routes:
        # Seed default realistic routes if empty
        r1 = TransitRoute(
            route_number="BUS-101",
            name="Metro Express Line 1",
            origin="North Hub",
            destination="Central Station",
            distance_km=18.5,
            active_buses=12,
            waypoints=[[9.9816, 76.2999], [9.9850, 76.3050], [9.9900, 76.3120]],
        )
        r2 = TransitRoute(
            route_number="BUS-204",
            name="Coastal Ring Corridor",
            origin="Harbor Gate",
            destination="Tech Park East",
            distance_km=24.2,
            active_buses=8,
            waypoints=[[9.9700, 76.2800], [9.9750, 76.2900], [9.9820, 76.3000]],
        )
        db.add_all([r1, r2])
        await db.commit()
        routes = [r1, r2]
    return [
        TransitRouteRead(
            id=str(r.id),
            route_number=r.route_number,
            name=r.name,
            origin=r.origin,
            destination=r.destination,
            distance_km=r.distance_km,
            active_buses=r.active_buses,
            status=r.status,
            waypoints=r.waypoints or [],
            created_at=r.created_at,
        )
        for r in routes
    ]


@router.get(
    "/api/v1/stops",
    response_model=list[BusStopRead],
    dependencies=[Depends(require_permission("transit.read"))],
)
async def list_bus_stops(db: AsyncSession = Depends(get_db)):
    stmt = select(BusStop).order_by(BusStop.code.asc())
    stops = (await db.scalars(stmt)).all()
    if not stops:
        s1 = BusStop(
            code="STOP-01",
            name="Central Station Terminal",
            latitude=9.9816,
            longitude=76.2999,
            route_code="BUS-101",
            passenger_count=142,
        )
        s2 = BusStop(
            code="STOP-02",
            name="City Hospital South",
            latitude=9.9850,
            longitude=76.3050,
            route_code="BUS-101",
            passenger_count=88,
        )
        s3 = BusStop(
            code="STOP-03",
            name="Financial District Interchange",
            latitude=9.9900,
            longitude=76.3120,
            route_code="BUS-204",
            passenger_count=215,
        )
        db.add_all([s1, s2, s3])
        await db.commit()
        stops = [s1, s2, s3]
    return [
        BusStopRead(
            id=str(s.id),
            code=s.code,
            name=s.name,
            latitude=s.latitude,
            longitude=s.longitude,
            route_code=s.route_code,
            passenger_count=s.passenger_count,
            created_at=s.created_at,
        )
        for s in stops
    ]


# -----------------------------------------------------------------------------
# Utilities (Water & Energy)
# -----------------------------------------------------------------------------
@router.get(
    "/api/v1/water",
    response_model=list[WaterZoneRead],
    dependencies=[Depends(require_permission("water.read"))],
)
async def list_water_zones(db: AsyncSession = Depends(get_db)):
    stmt = select(WaterZone).order_by(WaterZone.zone_code.asc())
    zones = (await db.scalars(stmt)).all()
    if not zones:
        z1 = WaterZone(
            zone_code="WZ-NORTH",
            name="Northern Reservoir Zone",
            capacity_liters=4500000.0,
            consumption_lps=145.2,
            status="NORMAL",
            leak_risk="LOW",
            outages_active=0,
        )
        z2 = WaterZone(
            zone_code="WZ-CENTRAL",
            name="Central Municipal Distribution",
            capacity_liters=3200000.0,
            consumption_lps=210.8,
            status="WARNING",
            leak_risk="HIGH",
            outages_active=1,
        )
        db.add_all([z1, z2])
        await db.commit()
        zones = [z1, z2]
    return [
        WaterZoneRead(
            id=str(z.id),
            zone_code=z.zone_code,
            name=z.name,
            capacity_liters=z.capacity_liters,
            consumption_lps=z.consumption_lps,
            status=z.status,
            leak_risk=z.leak_risk,
            outages_active=z.outages_active,
            created_at=z.created_at,
        )
        for z in zones
    ]


@router.get(
    "/api/v1/energy",
    response_model=list[PowerSubstationRead],
    dependencies=[Depends(require_permission("energy.read"))],
)
async def list_power_substations(db: AsyncSession = Depends(get_db)):
    stmt = select(PowerSubstation).order_by(PowerSubstation.substation_code.asc())
    substations = (await db.scalars(stmt)).all()
    if not substations:
        ps1 = PowerSubstation(
            substation_code="SUB-01",
            name="Metro Main Grid Substation",
            capacity_mw=250.0,
            load_mw=184.5,
            status="OPERATIONAL",
            outage_risk="LOW",
        )
        ps2 = PowerSubstation(
            substation_code="SUB-02",
            name="Industrial Corridor Grid",
            capacity_mw=180.0,
            load_mw=162.0,
            status="HIGH_LOAD",
            outage_risk="MEDIUM",
        )
        db.add_all([ps1, ps2])
        await db.commit()
        substations = [ps1, ps2]
    return [
        PowerSubstationRead(
            id=str(ps.id),
            substation_code=ps.substation_code,
            name=ps.name,
            capacity_mw=ps.capacity_mw,
            load_mw=ps.load_mw,
            status=ps.status,
            outage_risk=ps.outage_risk,
            created_at=ps.created_at,
        )
        for ps in substations
    ]


# -----------------------------------------------------------------------------
# Environment
# -----------------------------------------------------------------------------
@router.get(
    "/api/v1/environment",
    response_model=list[EnvironmentReadingRead],
    dependencies=[Depends(require_permission("environment.read"))],
)
async def get_environment_readings(db: AsyncSession = Depends(get_db)):
    stmt = select(EnvironmentReading).order_by(EnvironmentReading.recorded_at.desc()).limit(10)
    readings = (await db.scalars(stmt)).all()
    if not readings:
        er1 = EnvironmentReading(
            zone_code="ZONE-NORTH",
            temperature_c=29.4,
            rainfall_mm=42.5,
            humidity_pct=88.0,
            aqi=58,
            flood_risk="HIGH",
        )
        er2 = EnvironmentReading(
            zone_code="ZONE-SOUTH",
            temperature_c=31.1,
            rainfall_mm=12.0,
            humidity_pct=72.0,
            aqi=42,
            flood_risk="LOW",
        )
        db.add_all([er1, er2])
        await db.commit()
        readings = [er1, er2]
    return [
        EnvironmentReadingRead(
            id=str(r.id),
            zone_code=r.zone_code,
            temperature_c=r.temperature_c,
            rainfall_mm=r.rainfall_mm,
            humidity_pct=r.humidity_pct,
            aqi=r.aqi,
            flood_risk=r.flood_risk,
            recorded_at=r.recorded_at,
        )
        for r in readings
    ]


# Infrastructure assets: see app/api/routes_infrastructure.py.
# City projects: see app/api/routes_projects.py.
# Both moved out once they got real create/update endpoints instead of a
# GET-only, self-seeding stub.


# -----------------------------------------------------------------------------
# Citizen Complaints
# -----------------------------------------------------------------------------
@router.get(
    "/api/v1/complaints",
    response_model=list[CitizenComplaintRead],
    dependencies=[Depends(require_permission("complaint.read"))],
)
async def list_complaints(db: AsyncSession = Depends(get_db)):
    stmt = select(CitizenComplaint).order_by(CitizenComplaint.created_at.desc())
    complaints = (await db.scalars(stmt)).all()
    if not complaints:
        c1 = CitizenComplaint(
            complaint_number="CMP-9041",
            title="Pothole near Hospital Gate",
            description="Deep pothole causing severe traffic slowdown on Road 1024.",
            category="Infrastructure",
            latitude=9.9850,
            longitude=76.3050,
            image_url="https://images.unsplash.com/photo-1515162816999-a0c47dc192f7?w=600",
            status="SUBMITTED",
            reporter_email="citizen@example.com",
            department_code="INFRASTRUCTURE",
        )
        db.add(c1)
        await db.commit()
        complaints = [c1]
    return [
        CitizenComplaintRead(
            id=str(c.id),
            complaint_number=c.complaint_number,
            title=c.title,
            description=c.description,
            category=c.category,
            latitude=c.latitude,
            longitude=c.longitude,
            image_url=c.image_url,
            status=c.status,
            reporter_email=c.reporter_email,
            department_code=c.department_code,
            created_at=c.created_at,
        )
        for c in complaints
    ]


@router.post(
    "/api/v1/complaints",
    response_model=CitizenComplaintRead,
    dependencies=[Depends(require_permission("complaint.create"))],
)
async def create_complaint(body: CitizenComplaintCreate, db: AsyncSession = Depends(get_db)):
    num = f"CMP-{uuid.uuid4().hex[:6].upper()}"
    complaint = CitizenComplaint(
        complaint_number=num,
        title=body.title,
        description=body.description,
        category=body.category,
        latitude=body.latitude,
        longitude=body.longitude,
        image_url=body.image_url,
        reporter_email=body.reporter_email,
        department_code="CITIZEN_SERVICES",
    )
    db.add(complaint)
    await db.commit()
    await db.refresh(complaint)
    return CitizenComplaintRead(
        id=str(complaint.id),
        complaint_number=complaint.complaint_number,
        title=complaint.title,
        description=complaint.description,
        category=complaint.category,
        latitude=complaint.latitude,
        longitude=complaint.longitude,
        image_url=complaint.image_url,
        status=complaint.status,
        reporter_email=complaint.reporter_email,
        department_code=complaint.department_code,
        created_at=complaint.created_at,
    )


# Workflow tasks: see app/api/routes_workflows.py -- moved out of this file
# once they got a real create/assign/status-transition API instead of a
# GET-only, self-seeding stub.


# -----------------------------------------------------------------------------
# Audit & Notifications
# -----------------------------------------------------------------------------
@router.get(
    "/api/v1/audit",
    response_model=list[AuditLogRead],
    dependencies=[Depends(require_permission("audit.read"))],
)
async def list_audit_logs(db: AsyncSession = Depends(get_db)):
    stmt = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(20)
    logs = (await db.scalars(stmt)).all()
    if not logs:
        a1 = AuditLog(
            actor="Officer #182",
            action="ROAD_CLOSED",
            target_resource="Road #1024",
            department_code="TRAFFIC",
            reason="Monsoon flood mitigation",
            approved_by="Traffic Admin",
        )
        a2 = AuditLog(
            actor="System AI Supervisor",
            action="CASCADE_RISK_TRIGGERED",
            target_resource="Zone 4",
            department_code="EMERGENCY",
            reason="Heavy rain + Hospital accessibility drop",
            approved_by="City Admin",
        )
        db.add_all([a1, a2])
        await db.commit()
        logs = [a1, a2]
    return [
        AuditLogRead(
            id=str(log.id),
            actor=log.actor,
            action=log.action,
            target_resource=log.target_resource,
            department_code=log.department_code,
            reason=log.reason,
            approved_by=log.approved_by,
            timestamp=log.timestamp,
        )
        for log in logs
    ]


# Notifications: see app/api/routes_notifications.py for the CRUD surface
# and app/services/notifications.py for the trigger rules that create them
# automatically (wired into routes_incidents.py, routes_roads.py, and
# routes_hospitals.py) -- moved out once it became a real engine instead of
# a GET-only, self-seeding stub.


# -----------------------------------------------------------------------------
# Simulation Engine
# -----------------------------------------------------------------------------
@router.get(
    "/api/v1/simulations",
    response_model=list[SimulationScenarioRead],
    dependencies=[Depends(require_permission("simulation.read"))],
)
async def list_simulations(db: AsyncSession = Depends(get_db)):
    stmt = select(SimulationScenario).order_by(SimulationScenario.created_at.desc())
    scenarios = (await db.scalars(stmt)).all()
    if not scenarios:
        s1 = SimulationScenario(
            scenario_code="SCEN-01",
            name="Monsoon Heavy Rain & Road Closure",
            description="Simulates closure of Road 1024 during a 50mm/hr rain event.",
            parameters={"road_closed": "Road 1024", "heavy_rain": True, "duration_hours": 24},
            results={
                "baseline_traffic": "72%",
                "scenario_traffic": "91%",
                "emergency_response_eta_min": 14.5,
                "hospital_accessibility": "79%",
            },
            status="COMPLETED",
        )
        db.add(s1)
        await db.commit()
        scenarios = [s1]
    return [
        SimulationScenarioRead(
            id=str(s.id),
            scenario_code=s.scenario_code,
            name=s.name,
            description=s.description,
            parameters=s.parameters,
            results=s.results,
            status=s.status,
            created_at=s.created_at,
        )
        for s in scenarios
    ]


@router.post(
    "/api/v1/simulations",
    response_model=SimulationScenarioRead,
    dependencies=[Depends(require_permission("simulation.create"))],
)
async def create_simulation(body: SimulationScenarioCreate, db: AsyncSession = Depends(get_db)):
    code = f"SCEN-{uuid.uuid4().hex[:6].upper()}"
    # Run deterministic simulation engine calculation
    rain = body.parameters.get("heavy_rain", False)
    road_closed = body.parameters.get("road_closed", None)
    traffic_pct = 92 if road_closed else (85 if rain else 70)
    eta_min = 16.2 if road_closed else (12.0 if rain else 8.5)
    accessibility = "78%" if road_closed else "92%"

    scenario = SimulationScenario(
        scenario_code=code,
        name=body.name,
        description=body.description,
        parameters=body.parameters,
        results={
            "baseline_traffic": "70%",
            "scenario_traffic": f"{traffic_pct}%",
            "emergency_response_eta_min": eta_min,
            "hospital_accessibility": accessibility,
            "cascading_risk": "HIGH" if (rain and road_closed) else "MEDIUM",
        },
        status="COMPLETED",
    )
    db.add(scenario)
    await db.commit()
    await db.refresh(scenario)
    return SimulationScenarioRead(
        id=str(scenario.id),
        scenario_code=scenario.scenario_code,
        name=scenario.name,
        description=scenario.description,
        parameters=scenario.parameters,
        results=scenario.results,
        status=scenario.status,
        created_at=scenario.created_at,
    )


# -----------------------------------------------------------------------------
# AI City Supervisor & Multi-Agent Engine
# -----------------------------------------------------------------------------
@router.post(
    "/api/v1/ai/analyze",
    response_model=AIAnalysisResponse,
    dependencies=[Depends(require_permission("ai.analyze"))],
)
async def analyze_city_state(body: AIAnalysisRequest):
    return AIAnalysisResponse(
        summary=(
            f"AI Supervisor evaluation for query: '{body.query}'. Detected active "
            "correlations across Traffic, Healthcare, and Emergency response metrics."
        ),
        risks_detected=[
            "Cascading Traffic Congestion on Arterial Corridors",
            "Elevated Emergency Response Times (+4.2 mins average)",
            "Hospital Bed Capacity Surge in Central Sector",
        ],
        affected_systems=["Traffic Operations", "Emergency Dispatch", "City Hospital Network"],
        recommendations=[
            "Activate dynamic traffic signal timing on North Corridor",
            "Pre-position 3 backup ambulances near South Interchange",
            "Issue advisory for non-emergency public transit re-routing",
        ],
        supporting_data={
            "active_incidents": 4,
            "avg_road_occupancy": "84.2%",
            "icu_bed_available": 14,
            "weather_warning": "Heavy Rainfall Expected (Zone 4)",
        },
        confidence=0.94,
    )


# -----------------------------------------------------------------------------
# RAG Knowledge Search
# -----------------------------------------------------------------------------
@router.get(
    "/api/v1/knowledge",
    response_model=list[KnowledgeDocumentRead],
    dependencies=[Depends(require_permission("knowledge.read"))],
)
async def list_knowledge_documents(db: AsyncSession = Depends(get_db)):
    stmt = select(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc())
    docs = (await db.scalars(stmt)).all()
    if not docs:
        k1 = KnowledgeDocument(
            doc_code="KNOW-DOC-01",
            title="Monsoon Emergency Management Standard Operating Procedure",
            category="EMERGENCY_SOP",
            content=(
                "During heavy rainfall events (>30mm/hr), emergency response units must "
                "auto-deploy to pre-designated low-elevation staging posts."
            ),
            tags=["Emergency", "Monsoon", "SOP"],
            vector_id="vec-monsoon-sop-01",
        )
        k2 = KnowledgeDocument(
            doc_code="KNOW-DOC-02",
            title="Urban Transit Priority & Signal Preemption Guidelines",
            category="TRAFFIC_POLICY",
            content=(
                "Ambulances and rapid transit buses are granted priority traffic signal "
                "preemption on primary arterial corridors."
            ),
            tags=["Traffic", "Transit", "Priority"],
            vector_id="vec-traffic-policy-02",
        )
        db.add_all([k1, k2])
        await db.commit()
        docs = [k1, k2]
    return [
        KnowledgeDocumentRead(
            id=str(d.id),
            doc_code=d.doc_code,
            title=d.title,
            category=d.category,
            content=d.content,
            tags=d.tags,
            vector_id=d.vector_id,
            created_at=d.created_at,
        )
        for d in docs
    ]


# Universal Search: see app/api/routes_search.py -- moved out and extended
# to cover vehicles, workflow tasks, infrastructure assets, and projects
# (it previously only covered roads/hospitals/incidents/complaints), and to
# require authentication, which it never did here.


# -----------------------------------------------------------------------------
# Universal Analytics
# -----------------------------------------------------------------------------
@router.get("/api/v1/analytics", dependencies=[Depends(require_permission("analytics.read"))])
async def get_city_analytics(db: AsyncSession = Depends(get_db)):
    active_incidents = (
        await db.scalar(select(func.count(Incident.id)).where(Incident.status != "RESOLVED")) or 0
    )
    total_roads = await db.scalar(select(func.count(Road.id))) or 0
    total_hospitals = await db.scalar(select(func.count(Hospital.id))) or 0
    total_vehicles = await db.scalar(select(func.count(Vehicle.id))) or 0

    return {
        "kpis": {
            "active_incidents": active_incidents,
            "total_roads_monitored": total_roads,
            "total_hospitals_connected": total_hospitals,
            "active_vehicles_tracked": total_vehicles,
            "traffic_index": 74.2,
            "hospital_occupancy_pct": 82.5,
            "avg_response_time_min": 7.4,
            "flood_risk_level": "MODERATE",
        },
        "trends": {
            "traffic_by_hour": [
                {"hour": "00:00", "index": 20},
                {"hour": "04:00", "index": 15},
                {"hour": "08:00", "index": 88},
                {"hour": "12:00", "index": 65},
                {"hour": "16:00", "index": 92},
                {"hour": "20:00", "index": 55},
            ],
            "incident_severity_distribution": {
                "LOW": 40,
                "MEDIUM": 35,
                "HIGH": 18,
                "CRITICAL": 7,
            },
        },
    }
