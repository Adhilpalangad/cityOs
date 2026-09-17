from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import PageMeta


# Transit
class TransitRouteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    route_number: str
    name: str
    origin: str
    destination: str
    distance_km: float
    active_buses: int
    status: str
    waypoints: list
    created_at: datetime


class TransitRouteListResponse(BaseModel):
    items: list[TransitRouteRead]
    meta: PageMeta


class BusStopRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    name: str
    latitude: float
    longitude: float
    route_code: str | None = None
    passenger_count: int
    created_at: datetime


# Utilities
class WaterZoneRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    zone_code: str
    name: str
    capacity_liters: float
    consumption_lps: float
    status: str
    leak_risk: str
    outages_active: int
    created_at: datetime


class PowerSubstationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    substation_code: str
    name: str
    capacity_mw: float
    load_mw: float
    status: str
    outage_risk: str
    created_at: datetime


# Environment
class EnvironmentReadingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    zone_code: str
    temperature_c: float
    rainfall_mm: float
    humidity_pct: float
    aqi: int
    flood_risk: str
    recorded_at: datetime


# Finance
class CityProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_code: str
    name: str
    department_code: str
    budget: float
    spent: float
    status: str
    completion_percentage: float
    created_at: datetime


# Complaints & Workflows
class CitizenComplaintCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=150)
    description: str = Field(..., min_length=5)
    category: str = Field(default="General")
    latitude: float | None = None
    longitude: float | None = None
    image_url: str | None = None
    reporter_email: str | None = None


class CitizenComplaintRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    complaint_number: str
    title: str
    description: str
    category: str
    latitude: float | None = None
    longitude: float | None = None
    image_url: str | None = None
    status: str
    reporter_email: str | None = None
    department_code: str | None = None
    created_at: datetime


# Audit & Notifications
class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    actor: str
    action: str
    target_resource: str
    department_code: str | None = None
    reason: str | None = None
    approved_by: str | None = None
    timestamp: datetime


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    message: str
    severity: str
    target_department: str | None = None
    channel: str
    is_read: bool
    created_at: datetime


# Simulations & AI
class SimulationScenarioCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=150)
    description: str | None = None
    parameters: dict = Field(default_factory=dict)


class SimulationScenarioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    scenario_code: str
    name: str
    description: str | None = None
    parameters: dict
    results: dict
    status: str
    created_at: datetime


class KnowledgeDocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    doc_code: str
    title: str
    category: str
    content: str
    tags: list
    vector_id: str | None = None
    created_at: datetime


class AIAnalysisRequest(BaseModel):
    query: str
    context: dict | None = None


class AIAnalysisResponse(BaseModel):
    summary: str
    risks_detected: list[str]
    affected_systems: list[str]
    recommendations: list[str]
    supporting_data: dict
    confidence: float
