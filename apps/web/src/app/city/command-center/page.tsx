import {
  getAnalytics, getIncidents, getNotifications,
  getHospitals, getRoads
} from "@/lib/city-api";
import { severityColor, statusColor } from "@/lib/colors";
import {
  AlertTriangle, Wifi, HeartPulse, Car,
  CloudRain, Activity, TrendingUp, Bell
} from "lucide-react";
import { RoadNetworkLive } from "./RoadNetworkLive";

export const metadata = {
  title: "Command Center | CityOS",
  description: "City-wide operational overview: live incidents, KPIs, department status and AI alerts.",
};

export default async function CommandCenterPage() {
  const [analytics, incidentsRes, notifications, hospitalsRes, roadsRes] = await Promise.all([
    getAnalytics(),
    getIncidents(1, undefined),
    getNotifications(),
    getHospitals(),
    getRoads(1),
  ]);

  const kpis = analytics?.kpis;
  const incidents = incidentsRes?.items ?? [];
  const notifs = notifications ?? [];
  const hospitals = hospitalsRes?.items ?? [];
  const roads = roadsRes?.items ?? [];

  const criticalIncidents = incidents.filter((i) => i.severity === "CRITICAL").length;

  return (
    <div className="min-h-screen p-6 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-brand">Live Operations</p>
          <h1 className="mt-1 text-2xl font-bold text-ink">City Command Center</h1>
          <p className="mt-1 text-sm text-ink-muted">Real-time city health, incidents, and department status</p>
        </div>
        <div className="flex items-center gap-2 rounded-lg border border-line bg-surface px-3 py-2 text-xs text-ink-muted">
          <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          Live · {new Date().toLocaleTimeString()}
        </div>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <KpiCard
          icon={<AlertTriangle size={18} className="text-red-400" />}
          label="Active Incidents"
          value={kpis?.active_incidents ?? "—"}
          sub={`${criticalIncidents} critical`}
          accent="red"
        />
        <KpiCard
          icon={<Car size={18} className="text-amber-400" />}
          label="Traffic Index"
          value={kpis ? `${kpis.traffic_index}%` : "—"}
          sub="City-wide load"
          accent="amber"
        />
        <KpiCard
          icon={<HeartPulse size={18} className="text-pink-400" />}
          label="Hospital Occupancy"
          value={kpis ? `${kpis.hospital_occupancy_pct}%` : "—"}
          sub="Bed utilization"
          accent="pink"
        />
        <KpiCard
          icon={<Activity size={18} className="text-sky-400" />}
          label="Avg Response Time"
          value={kpis ? `${kpis.avg_response_time_min} min` : "—"}
          sub="Emergency ETA"
          accent="sky"
        />
      </div>

      {/* Second row KPIs */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <KpiCard
          icon={<Wifi size={18} className="text-emerald-400" />}
          label="Roads Monitored"
          value={kpis?.total_roads_monitored ?? "—"}
          sub="Connected roads"
          accent="emerald"
        />
        <KpiCard
          icon={<HeartPulse size={18} className="text-violet-400" />}
          label="Hospitals Connected"
          value={kpis?.total_hospitals_connected ?? "—"}
          sub="Network nodes"
          accent="violet"
        />
        <KpiCard
          icon={<TrendingUp size={18} className="text-cyan-400" />}
          label="Vehicles Tracked"
          value={kpis?.active_vehicles_tracked ?? "—"}
          sub="Active fleet"
          accent="cyan"
        />
        <KpiCard
          icon={<CloudRain size={18} className="text-blue-400" />}
          label="Flood Risk"
          value={kpis?.flood_risk_level ?? "—"}
          sub="Environmental"
          accent={kpis?.flood_risk_level === "HIGH" || kpis?.flood_risk_level === "CRITICAL" ? "red" : "blue"}
        />
      </div>

      {/* Main content: incidents + notifications */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Active Incidents */}
        <div className="lg:col-span-2 rounded-xl border border-line bg-surface p-5">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-ink">Active Incidents</h2>
            <span className="rounded-full bg-surface-muted px-2 py-0.5 text-xs text-ink-muted">
              {incidents.length} total
            </span>
          </div>
          <div className="space-y-2">
            {incidents.slice(0, 8).length > 0 ? incidents.slice(0, 8).map((inc) => (
              <div key={inc.id} className="flex items-center gap-3 rounded-lg bg-surface-muted/60 px-3 py-2.5">
                <span className={`rounded-md border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide ${severityColor(inc.severity)}`}>
                  {inc.severity}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="truncate text-xs font-medium text-ink">{inc.incident_number}</p>
                  <p className="text-[10px] text-ink-muted">{inc.incident_type.replace(/_/g, " ")}</p>
                </div>
                <span className={`rounded-full border px-2 py-0.5 text-[10px] font-medium ${statusColor(inc.status)}`}>
                  {inc.status}
                </span>
              </div>
            )) : (
              <div className="flex h-24 items-center justify-center text-sm text-ink-faint">
                No incidents — start services and run a migration to see live data
              </div>
            )}
          </div>
        </div>

        {/* Live Notifications */}
        <div className="rounded-xl border border-line bg-surface p-5">
          <div className="mb-4 flex items-center gap-2">
            <Bell size={14} className="text-brand" />
            <h2 className="text-sm font-semibold text-ink">Live Alerts</h2>
          </div>
          <div className="space-y-2">
            {notifs.slice(0, 8).map((n) => (
              <div key={n.id} className="rounded-lg bg-surface-muted/60 p-3">
                <div className="flex items-start justify-between gap-2">
                  <p className="text-xs font-medium text-ink leading-snug">{n.title}</p>
                  <span className={`shrink-0 rounded-full border px-1.5 py-0.5 text-[9px] font-bold uppercase ${severityColor(n.severity)}`}>
                    {n.severity}
                  </span>
                </div>
                <p className="mt-1 text-[10px] text-ink-muted leading-relaxed">{n.message}</p>
              </div>
            ))}
            {notifs.length === 0 && (
              <div className="flex h-20 items-center justify-center text-xs text-ink-faint">
                No alerts right now
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Hospital Network */}
      <div className="rounded-xl border border-line bg-surface p-5">
        <h2 className="mb-4 text-sm font-semibold text-ink">Hospital Network Status</h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {hospitals.map((h) => {
            const bedPct = Math.round((h.beds_occupied / Math.max(h.beds_total, 1)) * 100);
            const icuPct = Math.round((h.icu_occupied / Math.max(h.icu_total, 1)) * 100);
            return (
              <div key={h.id} className="rounded-lg bg-surface-muted/60 p-3">
                <p className="text-xs font-semibold text-ink truncate">{h.name}</p>
                <p className="mt-0.5 text-[10px] text-ink-faint">{h.code}</p>
                <div className="mt-2 space-y-1.5">
                  <ProgressBar label="Beds" pct={bedPct} />
                  <ProgressBar label="ICU" pct={icuPct} critical={icuPct > 85} />
                </div>
                <span className={`mt-2 inline-block rounded-full border px-2 py-0.5 text-[10px] font-medium ${statusColor(h.status)}`}>
                  {h.status}
                </span>
              </div>
            );
          })}
          {hospitals.length === 0 && (
            <p className="col-span-full text-center text-sm text-ink-faint py-6">
              No hospitals seeded — run migration & start city-core service
            </p>
          )}
        </div>
      </div>

      {/* Roads -- live via useLiveFeed(), see apps/web/src/lib/live-socket.ts */}
      <RoadNetworkLive initialRoads={roads} />
    </div>
  );
}

function KpiCard({
  icon, label, value, sub,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  sub: string;
  accent?: string;
}) {
  return (
    <div className="rounded-xl border border-line bg-surface p-4 hover:border-brand/30 transition-colors">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-ink-muted">{label}</span>
        {icon}
      </div>
      <p className="mt-2 text-2xl font-bold text-ink tracking-tight">{value}</p>
      <p className="mt-0.5 text-[11px] text-ink-faint">{sub}</p>
    </div>
  );
}

function ProgressBar({ label, pct, critical = false }: { label: string; pct: number; critical?: boolean }) {
  const color = critical ? "bg-red-500" : pct > 75 ? "bg-orange-400" : "bg-brand";
  return (
    <div>
      <div className="flex justify-between text-[10px] text-ink-muted mb-0.5">
        <span>{label}</span>
        <span>{pct}%</span>
      </div>
      <div className="h-1.5 w-full rounded-full bg-surface-muted">
        <div className={`h-1.5 rounded-full ${color} transition-all`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
