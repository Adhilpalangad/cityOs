import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

# Plain strings, validated by Pydantic at the API boundary -- see the note
# in identity's models.py for why (portable across SQLite and PostgreSQL,
# no migration needed to add a value).
ROAD_STATUSES = ("OPEN", "CLOSED", "MAINTENANCE")
TRAFFIC_LEVELS = ("LOW", "MEDIUM", "HIGH", "CRITICAL")
RISK_LEVELS = ("LOW", "MEDIUM", "HIGH", "CRITICAL")
HOSPITAL_STATUSES = ("OPERATIONAL", "LIMITED", "CLOSED")
CAPACITY_LEVELS = ("LOW", "MEDIUM", "HIGH", "CRITICAL")
VEHICLE_TYPES = ("public_transport", "ambulance", "private", "fleet")
VEHICLE_STATUSES = ("ACTIVE", "INACTIVE", "MAINTENANCE")
INCIDENT_TYPES = (
    "ROAD_ACCIDENT",
    "FIRE",
    "FLOOD",
    "MEDICAL_EMERGENCY",
    "INFRASTRUCTURE_FAILURE",
    "PUBLIC_SAFETY",
)
INCIDENT_SEVERITIES = ("LOW", "MEDIUM", "HIGH", "CRITICAL")
# Lifecycle order from spec section 16. See app/services/incidents.py for
# the allowed-transition map that enforces this at the API layer.
INCIDENT_STATUSES = ("DETECTED", "VERIFIED", "ASSIGNED", "RESPONDING", "RESOLVED", "ANALYZED")
WORKFLOW_PRIORITIES = ("LOW", "MEDIUM", "HIGH", "CRITICAL")
# See app/services/workflows.py for the allowed-transition map this enforces.
WORKFLOW_STATUSES = ("PENDING", "IN_PROGRESS", "ESCALATED", "COMPLETED", "REJECTED")
ASSET_CONDITIONS = ("EXCELLENT", "GOOD", "FAIR", "POOR", "CRITICAL")
PROJECT_STATUSES = ("PLANNED", "IN_PROGRESS", "ON_HOLD", "COMPLETED", "CANCELLED")
NOTIFICATION_SEVERITIES = ("INFO", "WARNING", "CRITICAL")
NOTIFICATION_CHANNELS = ("IN_APP", "EMAIL", "SMS", "PUSH")
# See app/services/complaints.py for the allowed-transition map this enforces.
COMPLAINT_STATUSES = ("SUBMITTED", "IN_REVIEW", "ASSIGNED", "RESOLVED", "REJECTED")


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(sa.Uuid(), primary_key=True, default=uuid.uuid4)


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Road(Base):
    __tablename__ = "roads"

    id: Mapped[uuid.UUID] = _uuid_pk()
    code: Mapped[str] = mapped_column(sa.String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(sa.String(150), nullable=False)
    road_type: Mapped[str] = mapped_column(sa.String(30), nullable=False, default="local")
    status: Mapped[str] = mapped_column(sa.String(20), nullable=False, default="OPEN")
    capacity: Mapped[int] = mapped_column(sa.Integer(), nullable=False, default=0)
    current_vehicle_count: Mapped[int] = mapped_column(sa.Integer(), nullable=False, default=0)
    average_speed_kmh: Mapped[float | None] = mapped_column(sa.Float(), nullable=True)
    traffic_level: Mapped[str] = mapped_column(sa.String(20), nullable=False, default="LOW")
    risk_level: Mapped[str] = mapped_column(sa.String(20), nullable=False, default="LOW")
    # [[lat, lon], ...] waypoints tracing the road. A placeholder for a real
    # PostGIS LINESTRING column -- see services/city-core/README.md.
    waypoints: Mapped[list] = mapped_column(sa.JSON(), nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=_utcnow
    )

    __table_args__ = (
        sa.CheckConstraint(f"status IN {ROAD_STATUSES}", name="ck_roads_status"),
        sa.CheckConstraint(f"traffic_level IN {TRAFFIC_LEVELS}", name="ck_roads_traffic_level"),
        sa.CheckConstraint(f"risk_level IN {RISK_LEVELS}", name="ck_roads_risk_level"),
    )


class Hospital(Base):
    __tablename__ = "hospitals"

    id: Mapped[uuid.UUID] = _uuid_pk()
    code: Mapped[str] = mapped_column(sa.String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(sa.String(150), nullable=False)
    latitude: Mapped[float] = mapped_column(sa.Float(), nullable=False)
    longitude: Mapped[float] = mapped_column(sa.Float(), nullable=False)
    beds_total: Mapped[int] = mapped_column(sa.Integer(), nullable=False, default=0)
    beds_occupied: Mapped[int] = mapped_column(sa.Integer(), nullable=False, default=0)
    icu_total: Mapped[int] = mapped_column(sa.Integer(), nullable=False, default=0)
    icu_occupied: Mapped[int] = mapped_column(sa.Integer(), nullable=False, default=0)
    emergency_capacity: Mapped[str] = mapped_column(sa.String(20), nullable=False, default="LOW")
    status: Mapped[str] = mapped_column(sa.String(20), nullable=False, default="OPERATIONAL")
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=_utcnow
    )

    __table_args__ = (
        sa.CheckConstraint(f"status IN {HOSPITAL_STATUSES}", name="ck_hospitals_status"),
        sa.CheckConstraint(
            f"emergency_capacity IN {CAPACITY_LEVELS}", name="ck_hospitals_emergency_capacity"
        ),
        sa.CheckConstraint("beds_occupied <= beds_total", name="ck_hospitals_beds_bounds"),
        sa.CheckConstraint("icu_occupied <= icu_total", name="ck_hospitals_icu_bounds"),
    )


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[uuid.UUID] = _uuid_pk()
    vehicle_id: Mapped[str] = mapped_column(sa.String(50), unique=True, nullable=False, index=True)
    vehicle_type: Mapped[str] = mapped_column(sa.String(30), nullable=False)
    status: Mapped[str] = mapped_column(sa.String(20), nullable=False, default="ACTIVE")
    latitude: Mapped[float | None] = mapped_column(sa.Float(), nullable=True)
    longitude: Mapped[float | None] = mapped_column(sa.Float(), nullable=True)
    speed_kmh: Mapped[float | None] = mapped_column(sa.Float(), nullable=True)
    heading_degrees: Mapped[float | None] = mapped_column(sa.Float(), nullable=True)
    position_updated_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=_utcnow
    )

    __table_args__ = (
        sa.CheckConstraint(f"vehicle_type IN {VEHICLE_TYPES}", name="ck_vehicles_type"),
        sa.CheckConstraint(f"status IN {VEHICLE_STATUSES}", name="ck_vehicles_status"),
    )


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[uuid.UUID] = _uuid_pk()
    incident_number: Mapped[str] = mapped_column(
        sa.String(30), unique=True, nullable=False, index=True
    )
    incident_type: Mapped[str] = mapped_column(sa.String(30), nullable=False)
    severity: Mapped[str] = mapped_column(sa.String(20), nullable=False)
    status: Mapped[str] = mapped_column(sa.String(20), nullable=False, default="DETECTED")
    description: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    latitude: Mapped[float | None] = mapped_column(sa.Float(), nullable=True)
    longitude: Mapped[float | None] = mapped_column(sa.Float(), nullable=True)
    road_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid(), sa.ForeignKey("roads.id", ondelete="SET NULL"), nullable=True
    )
    # Departments and users live in the identity service; city-core has no
    # database it could foreign-key into there, so these are plain codes,
    # validated against identity at the API layer if/when that matters.
    reporter: Mapped[str | None] = mapped_column(sa.String(150), nullable=True)
    department_code: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)
    assigned_to: Mapped[str | None] = mapped_column(sa.String(150), nullable=True)
    response_time_seconds: Mapped[int | None] = mapped_column(sa.Integer(), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    # Spec section 16 lists "Evidence" as an incident field. Same shape as
    # CitizenComplaint.image_url -- a URL, not the image itself (Cloudinary
    # or equivalent owns the actual file; this repo has no media upload
    # pipeline yet, so providers/operators pass a URL directly for now).
    image_url: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=_utcnow
    )

    __table_args__ = (
        sa.CheckConstraint(f"incident_type IN {INCIDENT_TYPES}", name="ck_incidents_type"),
        sa.CheckConstraint(f"severity IN {INCIDENT_SEVERITIES}", name="ck_incidents_severity"),
        sa.CheckConstraint(f"status IN {INCIDENT_STATUSES}", name="ck_incidents_status"),
    )


class TransitRoute(Base):
    __tablename__ = "transit_routes"

    id: Mapped[uuid.UUID] = _uuid_pk()
    route_number: Mapped[str] = mapped_column(
        sa.String(30), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(sa.String(150), nullable=False)
    origin: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    destination: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    distance_km: Mapped[float] = mapped_column(sa.Float(), nullable=False, default=0.0)
    active_buses: Mapped[int] = mapped_column(sa.Integer(), nullable=False, default=0)
    status: Mapped[str] = mapped_column(sa.String(20), nullable=False, default="ACTIVE")
    waypoints: Mapped[list] = mapped_column(sa.JSON(), nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=_utcnow
    )


class BusStop(Base):
    __tablename__ = "bus_stops"

    id: Mapped[uuid.UUID] = _uuid_pk()
    code: Mapped[str] = mapped_column(sa.String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(sa.String(150), nullable=False)
    latitude: Mapped[float] = mapped_column(sa.Float(), nullable=False)
    longitude: Mapped[float] = mapped_column(sa.Float(), nullable=False)
    route_code: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)
    passenger_count: Mapped[int] = mapped_column(sa.Integer(), nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )


class WaterZone(Base):
    __tablename__ = "water_zones"

    id: Mapped[uuid.UUID] = _uuid_pk()
    zone_code: Mapped[str] = mapped_column(sa.String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(sa.String(150), nullable=False)
    capacity_liters: Mapped[float] = mapped_column(sa.Float(), nullable=False, default=1000000.0)
    consumption_lps: Mapped[float] = mapped_column(sa.Float(), nullable=False, default=50.0)
    status: Mapped[str] = mapped_column(sa.String(20), nullable=False, default="NORMAL")
    leak_risk: Mapped[str] = mapped_column(sa.String(20), nullable=False, default="LOW")
    outages_active: Mapped[int] = mapped_column(sa.Integer(), nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=_utcnow
    )


class PowerSubstation(Base):
    __tablename__ = "power_substations"

    id: Mapped[uuid.UUID] = _uuid_pk()
    substation_code: Mapped[str] = mapped_column(
        sa.String(50), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(sa.String(150), nullable=False)
    capacity_mw: Mapped[float] = mapped_column(sa.Float(), nullable=False, default=100.0)
    load_mw: Mapped[float] = mapped_column(sa.Float(), nullable=False, default=45.0)
    status: Mapped[str] = mapped_column(sa.String(20), nullable=False, default="OPERATIONAL")
    outage_risk: Mapped[str] = mapped_column(sa.String(20), nullable=False, default="LOW")
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=_utcnow
    )


class EnvironmentReading(Base):
    __tablename__ = "environment_readings"

    id: Mapped[uuid.UUID] = _uuid_pk()
    zone_code: Mapped[str] = mapped_column(sa.String(50), nullable=False, index=True)
    temperature_c: Mapped[float] = mapped_column(sa.Float(), nullable=False, default=28.0)
    rainfall_mm: Mapped[float] = mapped_column(sa.Float(), nullable=False, default=0.0)
    humidity_pct: Mapped[float] = mapped_column(sa.Float(), nullable=False, default=65.0)
    aqi: Mapped[int] = mapped_column(sa.Integer(), nullable=False, default=45)
    flood_risk: Mapped[str] = mapped_column(sa.String(20), nullable=False, default="LOW")
    recorded_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )


class InfrastructureAsset(Base):
    __tablename__ = "infrastructure_assets"

    id: Mapped[uuid.UUID] = _uuid_pk()
    asset_code: Mapped[str] = mapped_column(sa.String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(sa.String(150), nullable=False)
    asset_type: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    department_code: Mapped[str] = mapped_column(
        sa.String(50), nullable=False, default="INFRASTRUCTURE"
    )
    condition: Mapped[str] = mapped_column(sa.String(20), nullable=False, default="GOOD")
    risk_level: Mapped[str] = mapped_column(sa.String(20), nullable=False, default="LOW")
    latitude: Mapped[float | None] = mapped_column(sa.Float(), nullable=True)
    longitude: Mapped[float | None] = mapped_column(sa.Float(), nullable=True)
    estimated_cost: Mapped[float] = mapped_column(sa.Float(), nullable=False, default=0.0)
    next_maintenance: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=_utcnow
    )

    __table_args__ = (
        sa.CheckConstraint(
            f"condition IN {ASSET_CONDITIONS}", name="ck_infrastructure_assets_condition"
        ),
        sa.CheckConstraint(
            f"risk_level IN {RISK_LEVELS}", name="ck_infrastructure_assets_risk_level"
        ),
    )


class CityProject(Base):
    __tablename__ = "city_projects"

    id: Mapped[uuid.UUID] = _uuid_pk()
    project_code: Mapped[str] = mapped_column(
        sa.String(50), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(sa.String(150), nullable=False)
    department_code: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    budget: Mapped[float] = mapped_column(sa.Float(), nullable=False, default=0.0)
    spent: Mapped[float] = mapped_column(sa.Float(), nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(sa.String(30), nullable=False, default="IN_PROGRESS")
    completion_percentage: Mapped[float] = mapped_column(sa.Float(), nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=_utcnow
    )

    __table_args__ = (
        sa.CheckConstraint(f"status IN {PROJECT_STATUSES}", name="ck_city_projects_status"),
    )


class CitizenComplaint(Base):
    __tablename__ = "citizen_complaints"

    id: Mapped[uuid.UUID] = _uuid_pk()
    complaint_number: Mapped[str] = mapped_column(
        sa.String(30), unique=True, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(sa.String(150), nullable=False)
    description: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    category: Mapped[str] = mapped_column(sa.String(50), nullable=False, default="General")
    latitude: Mapped[float | None] = mapped_column(sa.Float(), nullable=True)
    longitude: Mapped[float | None] = mapped_column(sa.Float(), nullable=True)
    image_url: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    status: Mapped[str] = mapped_column(sa.String(20), nullable=False, default="SUBMITTED")
    reporter_email: Mapped[str | None] = mapped_column(sa.String(150), nullable=True)
    department_code: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=_utcnow
    )

    __table_args__ = (
        sa.CheckConstraint(
            f"status IN {COMPLAINT_STATUSES}", name="ck_citizen_complaints_status"
        ),
    )


class WorkflowTask(Base):
    __tablename__ = "workflow_tasks"

    id: Mapped[uuid.UUID] = _uuid_pk()
    task_number: Mapped[str] = mapped_column(sa.String(30), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(sa.String(150), nullable=False)
    department_code: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    assigned_to: Mapped[str | None] = mapped_column(sa.String(150), nullable=True)
    priority: Mapped[str] = mapped_column(sa.String(20), nullable=False, default="MEDIUM")
    status: Mapped[str] = mapped_column(sa.String(20), nullable=False, default="PENDING")
    sla_deadline: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=_utcnow
    )

    __table_args__ = (
        sa.CheckConstraint(f"priority IN {WORKFLOW_PRIORITIES}", name="ck_workflow_tasks_priority"),
        sa.CheckConstraint(f"status IN {WORKFLOW_STATUSES}", name="ck_workflow_tasks_status"),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = _uuid_pk()
    actor: Mapped[str] = mapped_column(sa.String(150), nullable=False)
    action: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    target_resource: Mapped[str] = mapped_column(sa.String(150), nullable=False)
    department_code: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)
    reason: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    approved_by: Mapped[str | None] = mapped_column(sa.String(150), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = _uuid_pk()
    title: Mapped[str] = mapped_column(sa.String(150), nullable=False)
    message: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    severity: Mapped[str] = mapped_column(sa.String(20), nullable=False, default="INFO")
    target_department: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)
    channel: Mapped[str] = mapped_column(sa.String(30), nullable=False, default="IN_APP")
    is_read: Mapped[bool] = mapped_column(sa.Boolean(), nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )

    __table_args__ = (
        sa.CheckConstraint(
            f"severity IN {NOTIFICATION_SEVERITIES}", name="ck_notifications_severity"
        ),
        sa.CheckConstraint(f"channel IN {NOTIFICATION_CHANNELS}", name="ck_notifications_channel"),
    )


class SimulationScenario(Base):
    __tablename__ = "simulation_scenarios"

    id: Mapped[uuid.UUID] = _uuid_pk()
    scenario_code: Mapped[str] = mapped_column(
        sa.String(50), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(sa.String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    parameters: Mapped[dict] = mapped_column(sa.JSON(), nullable=False, default=dict)
    results: Mapped[dict] = mapped_column(sa.JSON(), nullable=False, default=dict)
    status: Mapped[str] = mapped_column(sa.String(20), nullable=False, default="CREATED")
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=_utcnow
    )


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id: Mapped[uuid.UUID] = _uuid_pk()
    doc_code: Mapped[str] = mapped_column(sa.String(50), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(sa.String(150), nullable=False)
    category: Mapped[str] = mapped_column(sa.String(50), nullable=False, default="POLICY")
    content: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    tags: Mapped[list] = mapped_column(sa.JSON(), nullable=False, default=list)
    vector_id: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )
