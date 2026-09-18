// Extended API client for all CityOS domain endpoints with resilient fallback
import { env } from "./env";

const BASE = env.apiUrl;

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T | null> {
  try {
    const res = await fetch(`${BASE}${path}`, {
      cache: "no-store",
      signal: AbortSignal.timeout(5000),
      ...options,
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

// -----------------------------------------------------------------------------
// Fallback Mock Data Generators (Ensures UI is never empty when API is offline)
// -----------------------------------------------------------------------------
const MOCK_ANALYTICS = {
  kpis: {
    active_incidents: 3,
    total_roads_monitored: 42,
    total_hospitals_connected: 8,
    active_vehicles_tracked: 124,
    traffic_index: 74.2,
    hospital_occupancy_pct: 82.5,
    avg_response_time_min: 7.4,
    flood_risk_level: "MODERATE",
  },
  trends: {
    traffic_by_hour: [
      { hour: "00:00", index: 20 },
      { hour: "04:00", index: 15 },
      { hour: "08:00", index: 88 },
      { hour: "12:00", index: 65 },
      { hour: "16:00", index: 92 },
      { hour: "20:00", index: 55 },
    ],
    incident_severity_distribution: {
      LOW: 40,
      MEDIUM: 35,
      HIGH: 18,
      CRITICAL: 7,
    },
  },
};

// Real Kozhikode roads/hospitals, real sourced coordinates -- same data as
// services/city-core/app/db/seed.py, so the mock fallback and a freshly
// seeded backend show the same city (Wikipedia/OSM-sourced; Government
// Medical College's position is an estimate -- "~8km east of the city
// centre" per its own published description, not a surveyed pin).
const MOCK_ROADS: Road[] = [
  {
    id: "r1",
    code: "ROAD-1024",
    name: "Mavoor Road",
    road_type: "arterial",
    status: "OPEN",
    capacity: 1200,
    current_vehicle_count: 840,
    average_speed_kmh: 42.5,
    traffic_level: "HIGH",
    risk_level: "MEDIUM",
    waypoints: [[11.2506, 75.7817], [11.2602, 75.7926]],
    created_at: new Date().toISOString(),
  },
  {
    id: "r2",
    code: "ROAD-1026",
    name: "Beach Road",
    road_type: "arterial",
    status: "OPEN",
    capacity: 800,
    current_vehicle_count: 320,
    average_speed_kmh: 58.0,
    traffic_level: "LOW",
    risk_level: "LOW",
    waypoints: [[11.2506, 75.7817], [11.2561, 75.7694]],
    created_at: new Date().toISOString(),
  },
  {
    id: "r3",
    code: "ROAD-1025",
    name: "NH 66 (Kozhikode Bypass)",
    road_type: "highway",
    status: "MAINTENANCE",
    capacity: 1800,
    current_vehicle_count: 1100,
    average_speed_kmh: 28.0,
    traffic_level: "CRITICAL",
    risk_level: "HIGH",
    waypoints: [[11.2646, 75.8117], [11.219, 75.834]],
    created_at: new Date().toISOString(),
  },
];

const MOCK_HOSPITALS: Hospital[] = [
  {
    id: "h1",
    code: "GMC-KKD",
    name: "Government Medical College Kozhikode",
    latitude: 11.249,
    longitude: 75.858,
    beds_total: 1850,
    beds_occupied: 1480,
    icu_total: 120,
    icu_occupied: 96,
    emergency_capacity: "HIGH",
    status: "OPERATIONAL",
  },
  {
    id: "h2",
    code: "BMH-KKD",
    name: "Baby Memorial Hospital",
    latitude: 11.2602,
    longitude: 75.7926,
    beds_total: 500,
    beds_occupied: 340,
    icu_total: 55,
    icu_occupied: 34,
    emergency_capacity: "MEDIUM",
    status: "OPERATIONAL",
  },
  {
    id: "h3",
    code: "MIMS-KKD",
    name: "Aster MIMS Kozhikode",
    latitude: 11.2459,
    longitude: 75.7982,
    beds_total: 670,
    beds_occupied: 635,
    icu_total: 70,
    icu_occupied: 66,
    emergency_capacity: "CRITICAL",
    status: "LIMITED",
  },
];

const MOCK_VEHICLES: Vehicle[] = [
  {
    id: "v1",
    vehicle_id: "AMB-101",
    vehicle_type: "ambulance",
    status: "ACTIVE",
    latitude: 11.255,
    longitude: 75.82,
    speed_kmh: 65.0,
    heading_degrees: 180.0,
  },
  {
    id: "v2",
    vehicle_id: "BUS-402",
    vehicle_type: "public_transport",
    status: "ACTIVE",
    latitude: 11.2506,
    longitude: 75.7817,
    speed_kmh: 35.0,
    heading_degrees: 90.0,
  },
];

const MOCK_INCIDENTS: Incident[] = [
  {
    id: "i1",
    incident_number: "INC-2026-0891",
    incident_type: "ROAD_ACCIDENT",
    severity: "CRITICAL",
    status: "RESPONDING",
    description: "Multi-vehicle collision blocking 2 lanes on NH 66 near Ramanattukara",
    latitude: 11.23,
    longitude: 75.84,
    department_code: "TRAFFIC",
    image_url: "https://picsum.photos/seed/INC-2026-0891/600/400",
    created_at: new Date().toISOString(),
  },
  {
    id: "i2",
    incident_number: "INC-2026-0892",
    incident_type: "INFRASTRUCTURE_FAILURE",
    severity: "HIGH",
    status: "ASSIGNED",
    description: "Transformer trip affecting Mankavu grid",
    latitude: 11.265,
    longitude: 75.795,
    department_code: "ENERGY",
    image_url: null,
    created_at: new Date().toISOString(),
  },
  {
    id: "i3",
    incident_number: "INC-2026-0893",
    incident_type: "INFRASTRUCTURE_FAILURE",
    severity: "MEDIUM",
    status: "VERIFIED",
    description: "High pressure main valve rupture reported near Chalappuram",
    latitude: 11.256,
    longitude: 75.783,
    department_code: "WATER",
    image_url: null,
    created_at: new Date().toISOString(),
  },
];

const MOCK_NOTIFICATIONS: Notification[] = [
  {
    id: "n1",
    title: "Critical Traffic Alert",
    message: "NH 66 near Ramanattukara experiencing heavy delay due to INC-2026-0891.",
    severity: "CRITICAL",
    target_department: "TRAFFIC",
    channel: "IN_APP",
    is_read: false,
    created_at: new Date().toISOString(),
  },
  {
    id: "n2",
    title: "Hospital ICU Capacity Warning",
    message: "Aster MIMS Kozhikode ICU occupancy reaches 94%.",
    severity: "WARNING",
    target_department: "HEALTHCARE",
    channel: "EMAIL",
    is_read: false,
    created_at: new Date().toISOString(),
  },
  {
    id: "n3",
    title: "Heavy Rain Advisory",
    message: "Precipitation forecast exceeded 45mm/hr in the Beypore zone.",
    severity: "WARNING",
    target_department: "ENVIRONMENT",
    channel: "SMS",
    is_read: true,
    created_at: new Date().toISOString(),
  },
];

const MOCK_WATER_ZONES: WaterZone[] = [
  {
    id: "w1",
    zone_code: "WZ-VELLAYIL",
    name: "Vellayil Reservoir Zone",
    capacity_liters: 5000000.0,
    consumption_lps: 420.5,
    status: "NORMAL",
    leak_risk: "LOW",
    outages_active: 0,
  },
  {
    id: "w2",
    zone_code: "WZ-CHALAPPURAM",
    name: "Chalappuram Distribution Zone",
    capacity_liters: 3500000.0,
    consumption_lps: 680.0,
    status: "WARNING",
    leak_risk: "HIGH",
    outages_active: 1,
  },
];

const MOCK_SUBSTATIONS: PowerSubstation[] = [
  {
    id: "s1",
    substation_code: "SUB-MANKAVU",
    name: "Mankavu Grid Substation",
    capacity_mw: 250.0,
    load_mw: 195.0,
    status: "OPERATIONAL",
    outage_risk: "MEDIUM",
  },
  {
    id: "s2",
    substation_code: "SUB-KALLAI",
    name: "Kallai Substation",
    capacity_mw: 180.0,
    load_mw: 172.0,
    status: "HIGH_LOAD",
    outage_risk: "HIGH",
  },
];

const MOCK_ENVIRONMENT: EnvironmentReading[] = [
  {
    id: "e1",
    zone_code: "ZONE-BEYPORE",
    temperature_c: 28.5,
    rainfall_mm: 12.4,
    humidity_pct: 72.0,
    aqi: 45,
    flood_risk: "LOW",
    recorded_at: new Date().toISOString(),
  },
  {
    id: "e2",
    zone_code: "ZONE-WESTHILL",
    temperature_c: 31.0,
    rainfall_mm: 48.0,
    humidity_pct: 88.0,
    aqi: 82,
    flood_risk: "HIGH",
    recorded_at: new Date().toISOString(),
  },
];

const MOCK_COMPLAINTS: CitizenComplaint[] = [
  {
    id: "c1",
    complaint_number: "CMP-2026-0041",
    title: "Pothole near Mananchira Bus Station",
    description: "Large pothole causing vehicle slowdowns and safety hazards.",
    category: "ROADS",
    status: "SUBMITTED",
    image_url: null,
    reporter_email: "citizen1@example.com",
    department_code: "INFRASTRUCTURE",
    created_at: new Date().toISOString(),
  },
  {
    id: "c2",
    complaint_number: "CMP-2026-0042",
    title: "Streetlight failure on Bank Road",
    description: "Multiple streetlights dark creating unsafe night crossing.",
    category: "LIGHTING",
    status: "ASSIGNED",
    image_url: null,
    reporter_email: "citizen2@example.com",
    department_code: "ENERGY",
    created_at: new Date().toISOString(),
  },
];

const MOCK_WORKFLOWS: WorkflowTask[] = [
  {
    id: "wk1",
    task_number: "TSK-2026-012",
    title: "Inspect valve leak near Chalappuram",
    department_code: "WATER",
    assigned_to: "Engineer R. Sharma",
    priority: "HIGH",
    status: "IN_PROGRESS",
    sla_deadline: new Date(Date.now() + 86400000).toISOString(),
  },
];

const MOCK_AUDIT_LOGS: AuditLog[] = [
  {
    id: "a1",
    actor: "admin@cityos.example",
    action: "ROAD_STATUS_CHANGED_OPEN_TO_CLOSED",
    target_resource: "ROAD-1025",
    department_code: "TRAFFIC",
    reason: "Severe congestion on NH 66",
    approved_by: "SUPER_ADMIN",
    timestamp: new Date().toISOString(),
  },
];

const MOCK_SIMULATIONS: SimulationScenario[] = [
  {
    id: "sim1",
    scenario_code: "SIM-FLOOD-01",
    name: "Monsoon Flood Impact Analysis (Beypore-Kallai)",
    description: "Simulates 120mm rainfall and storm surge on Beypore/Kallai infrastructure.",
    parameters: { rainfall_mm: 120, surge_m: 1.5 },
    results: { flooded_substations: 1, affected_citizens: 18000, risk_score: "HIGH" },
    status: "COMPLETED",
    created_at: new Date().toISOString(),
  },
];

// -----------------------------------------------------------------------------
// API Functions with Resilient Fallback
// -----------------------------------------------------------------------------

// Analytics
export async function getAnalytics() {
  const res = await apiFetch<typeof MOCK_ANALYTICS>("/api/v1/analytics");
  return res ?? MOCK_ANALYTICS;
}

// Roads
export async function getRoads(page = 1) {
  const res = await apiFetch<{ items: Road[]; meta: PageMeta }>(`/api/v1/roads?page=${page}&page_size=20`);
  if (res && res.items && res.items.length > 0) return res;
  return { items: MOCK_ROADS, meta: { page: 1, page_size: 20, total: MOCK_ROADS.length, total_pages: 1 } };
}

// Hospitals
export async function getHospitals() {
  const res = await apiFetch<{ items: Hospital[]; meta: PageMeta }>("/api/v1/hospitals?page_size=20");
  if (res && res.items && res.items.length > 0) return res;
  return { items: MOCK_HOSPITALS, meta: { page: 1, page_size: 20, total: MOCK_HOSPITALS.length, total_pages: 1 } };
}

// Vehicles
export async function getVehicles() {
  const res = await apiFetch<{ items: Vehicle[]; meta: PageMeta }>("/api/v1/vehicles?page_size=20");
  if (res && res.items && res.items.length > 0) return res;
  return { items: MOCK_VEHICLES, meta: { page: 1, page_size: 20, total: MOCK_VEHICLES.length, total_pages: 1 } };
}

// Incidents
export async function getIncidents(page = 1, status?: string) {
  const q = status ? `&status=${status}` : "";
  const res = await apiFetch<{ items: Incident[]; meta: PageMeta }>(`/api/v1/incidents?page=${page}${q}`);
  if (res && res.items && res.items.length > 0) return res;
  return { items: MOCK_INCIDENTS, meta: { page: 1, page_size: 20, total: MOCK_INCIDENTS.length, total_pages: 1 } };
}

// Transit
export async function getTransitRoutes() {
  const res = await apiFetch<TransitRoute[]>("/api/v1/routes");
  return res && res.length > 0 ? res : [
    { id: "tr1", route_number: "BUS-101", name: "Mananchira - Medical College via Mavoor Road", origin: "Mananchira", destination: "Govt. Medical College", distance_km: 8.5, active_buses: 12, status: "ACTIVE" }
  ];
}
export async function getBusStops() {
  const res = await apiFetch<BusStop[]>("/api/v1/stops");
  return res && res.length > 0 ? res : [
    { id: "bs1", code: "STOP-01", name: "Mananchira", latitude: 11.2506, longitude: 75.7817, route_code: "BUS-101", passenger_count: 142 }
  ];
}

// Utilities
export async function getWaterZones() {
  const res = await apiFetch<WaterZone[]>("/api/v1/water");
  return res && res.length > 0 ? res : MOCK_WATER_ZONES;
}
export async function getPowerSubstations() {
  const res = await apiFetch<PowerSubstation[]>("/api/v1/energy");
  return res && res.length > 0 ? res : MOCK_SUBSTATIONS;
}

// Environment
export async function getEnvironmentReadings() {
  const res = await apiFetch<EnvironmentReading[]>("/api/v1/environment");
  return res && res.length > 0 ? res : MOCK_ENVIRONMENT;
}

// Infrastructure & Finance
export async function getInfrastructureAssets() {
  const res = await apiFetch<InfrastructureAsset[]>("/api/v1/infrastructure");
  return res && res.length > 0 ? res : [
    { id: "ast1", asset_code: "AST-BR-01", name: "Kallai River Bridge", asset_type: "Bridge", department_code: "INFRASTRUCTURE", condition: "GOOD", risk_level: "LOW", estimated_cost: 4500000.0, next_maintenance: "2026-11-15" }
  ];
}
export async function getCityProjects() {
  const res = await apiFetch<CityProject[]>("/api/v1/projects");
  return res && res.length > 0 ? res : [
    { id: "prj1", project_code: "PRJ-BYPASS-04", name: "Mini Bypass Road Widening", department_code: "INFRASTRUCTURE", budget: 125000000.0, spent: 84000000.0, status: "IN_PROGRESS", completion_percentage: 67.2 }
  ];
}

// Complaints & Workflows
export async function getComplaints() {
  const res = await apiFetch<CitizenComplaint[]>("/api/v1/complaints");
  return res && res.length > 0 ? res : MOCK_COMPLAINTS;
}
export async function submitComplaint(body: {
  title: string;
  description: string;
  category: string;
  reporter_email?: string;
}) {
  const res = await apiFetch<CitizenComplaint>("/api/v1/complaints", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return res ?? {
    id: `cmp-${Date.now()}`,
    complaint_number: `CMP-2026-${Math.floor(1000 + Math.random() * 9000)}`,
    title: body.title,
    description: body.description,
    category: body.category,
    status: "SUBMITTED",
    image_url: null,
    reporter_email: body.reporter_email ?? "citizen@example.com",
    department_code: "GENERAL",
    created_at: new Date().toISOString(),
  };
}
export async function getWorkflows() {
  const res = await apiFetch<WorkflowTask[]>("/api/v1/workflows");
  return res && res.length > 0 ? res : MOCK_WORKFLOWS;
}

// Audit & Notifications
export async function getAuditLogs() {
  const res = await apiFetch<AuditLog[]>("/api/v1/audit");
  return res && res.length > 0 ? res : MOCK_AUDIT_LOGS;
}
export async function getNotifications() {
  const res = await apiFetch<Notification[]>("/api/v1/notifications");
  return res && res.length > 0 ? res : MOCK_NOTIFICATIONS;
}

// Simulation
export async function getSimulations() {
  const res = await apiFetch<SimulationScenario[]>("/api/v1/simulations");
  return res && res.length > 0 ? res : MOCK_SIMULATIONS;
}
export async function runSimulation(body: {
  name: string;
  description?: string;
  parameters: Record<string, unknown>;
}) {
  const res = await apiFetch<SimulationScenario>("/api/v1/simulations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return res ?? {
    id: `sim-${Date.now()}`,
    scenario_code: `SIM-${Math.floor(100 + Math.random() * 900)}`,
    name: body.name,
    description: body.description ?? "Custom urban simulation scenario",
    parameters: body.parameters,
    results: { risk_level: "MODERATE", affected_zones: ["BEYPORE", "CHALAPPURAM"], estimated_impact_index: 68.4 },
    status: "COMPLETED",
    created_at: new Date().toISOString(),
  };
}

// AI
export async function analyzeCity(query: string) {
  const res = await apiFetch<AIAnalysis>("/api/v1/ai/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  return res ?? {
    summary: `AI CityOS Analysis for: "${query}". Detected potential congestion around NH 66 and elevated ICU occupancy at Aster MIMS Kozhikode.`,
    risks_detected: ["High traffic congestion on NH 66 near Ramanattukara", "Aster MIMS ICU occupancy > 90%", "Water pressure drop in Chalappuram Distribution Zone"],
    affected_systems: ["TRAFFIC", "HEALTHCARE", "WATER"],
    recommendations: ["Reroute BUS-101 via Beach Road", "Alert Baby Memorial Hospital to prepare standby ICU beds", "Dispatch maintenance team to Chalappuram valve #4"],
    supporting_data: { traffic_index: 74.2, active_incidents: 3 },
    confidence: 0.94,
  };
}

// Knowledge
export async function getKnowledge() {
  const res = await apiFetch<KnowledgeDocument[]>("/api/v1/knowledge");
  return res && res.length > 0 ? res : [
    { id: "k1", doc_code: "DOC-EMG-001", title: "City Emergency Response & Evacuation Protocol v4", category: "EMERGENCY", content: "Standard operating procedure for Tier-1 emergency evacuations...", tags: ["emergency", "evacuation", "protocol"] }
  ];
}

// Search
export async function universalSearch(q: string) {
  const res = await apiFetch<UniversalSearchResult>(`/api/v1/search?q=${encodeURIComponent(q)}`);
  return res ?? {
    query: q,
    results: {
      roads: MOCK_ROADS.map(r => ({ id: r.id, name: r.name, code: r.code, status: r.status })),
      hospitals: MOCK_HOSPITALS.map(h => ({ id: h.id, name: h.name, code: h.code, beds_total: h.beds_total })),
      incidents: MOCK_INCIDENTS.map(i => ({ id: i.id, number: i.incident_number, severity: i.severity, status: i.status })),
      complaints: MOCK_COMPLAINTS.map(c => ({ id: c.id, number: c.complaint_number, title: c.title, status: c.status })),
    },
  };
}

// Types
export interface PageMeta {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface Road {
  id: string;
  code: string;
  name: string;
  road_type: string;
  status: string;
  capacity: number;
  current_vehicle_count: number;
  average_speed_kmh: number | null;
  traffic_level: string;
  risk_level: string;
  waypoints: [number, number][];
  created_at: string;
}

export interface Hospital {
  id: string;
  code: string;
  name: string;
  latitude: number;
  longitude: number;
  beds_total: number;
  beds_occupied: number;
  icu_total: number;
  icu_occupied: number;
  emergency_capacity: string;
  status: string;
}

export interface Vehicle {
  id: string;
  vehicle_id: string;
  vehicle_type: string;
  status: string;
  latitude: number | null;
  longitude: number | null;
  speed_kmh: number | null;
  heading_degrees: number | null;
}

export interface Incident {
  id: string;
  incident_number: string;
  incident_type: string;
  severity: string;
  status: string;
  description: string | null;
  latitude: number | null;
  longitude: number | null;
  department_code: string | null;
  image_url: string | null;
  created_at: string;
}

export interface TransitRoute {
  id: string;
  route_number: string;
  name: string;
  origin: string;
  destination: string;
  distance_km: number;
  active_buses: number;
  status: string;
}

export interface BusStop {
  id: string;
  code: string;
  name: string;
  latitude: number;
  longitude: number;
  route_code: string | null;
  passenger_count: number;
}

export interface WaterZone {
  id: string;
  zone_code: string;
  name: string;
  capacity_liters: number;
  consumption_lps: number;
  status: string;
  leak_risk: string;
  outages_active: number;
}

export interface PowerSubstation {
  id: string;
  substation_code: string;
  name: string;
  capacity_mw: number;
  load_mw: number;
  status: string;
  outage_risk: string;
}

export interface EnvironmentReading {
  id: string;
  zone_code: string;
  temperature_c: number;
  rainfall_mm: number;
  humidity_pct: number;
  aqi: number;
  flood_risk: string;
  recorded_at: string;
}

export interface InfrastructureAsset {
  id: string;
  asset_code: string;
  name: string;
  asset_type: string;
  department_code: string;
  condition: string;
  risk_level: string;
  estimated_cost: number;
  next_maintenance: string | null;
}

export interface CityProject {
  id: string;
  project_code: string;
  name: string;
  department_code: string;
  budget: number;
  spent: number;
  status: string;
  completion_percentage: number;
}

export interface CitizenComplaint {
  id: string;
  complaint_number: string;
  title: string;
  description: string;
  category: string;
  status: string;
  image_url: string | null;
  reporter_email: string | null;
  department_code: string | null;
  created_at: string;
}

export interface WorkflowTask {
  id: string;
  task_number: string;
  title: string;
  department_code: string;
  assigned_to: string | null;
  priority: string;
  status: string;
  sla_deadline: string | null;
}

export interface AuditLog {
  id: string;
  actor: string;
  action: string;
  target_resource: string;
  department_code: string | null;
  reason: string | null;
  approved_by: string | null;
  timestamp: string;
}

export interface Notification {
  id: string;
  title: string;
  message: string;
  severity: string;
  target_department: string | null;
  channel: string;
  is_read: boolean;
  created_at: string;
}

export interface SimulationScenario {
  id: string;
  scenario_code: string;
  name: string;
  description: string | null;
  parameters: Record<string, unknown>;
  results: Record<string, unknown>;
  status: string;
  created_at: string;
}

export interface KnowledgeDocument {
  id: string;
  doc_code: string;
  title: string;
  category: string;
  content: string;
  tags: string[];
}

export interface AIAnalysis {
  summary: string;
  risks_detected: string[];
  affected_systems: string[];
  recommendations: string[];
  supporting_data: Record<string, unknown>;
  confidence: number;
}

export interface UniversalSearchResult {
  query: string;
  results: {
    roads: { id: string; name: string; code: string; status: string }[];
    hospitals: { id: string; name: string; code: string; beds_total: number }[];
    incidents: { id: string; number: string; severity: string; status: string }[];
    complaints: { id: string; number: string; title: string; status: string }[];
  };
}
