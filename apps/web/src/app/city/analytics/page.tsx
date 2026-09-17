import { getAnalytics } from "@/lib/city-api";
import { BarChart3, TrendingUp } from "lucide-react";

export const metadata = { title: "Analytics | CityOS", description: "City-wide analytics, traffic trends, and KPI dashboards." };

export default async function AnalyticsPage() {
  const analytics = await getAnalytics();
  const kpis = analytics?.kpis;
  const trends = analytics?.trends;
  const trafficTrend = trends?.traffic_by_hour ?? [];
  const maxTraffic = Math.max(...trafficTrend.map(t => t.index), 1);
  const severityDist = trends?.incident_severity_distribution ?? {};

  return (
    <div className="min-h-screen p-6 space-y-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-widest text-brand">Analytics Engine</p>
        <h1 className="mt-1 text-2xl font-bold text-ink">City Analytics</h1>
        <p className="mt-1 text-sm text-ink-muted">Traffic trends, incident patterns, and city-wide KPI metrics</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Kpi label="Active Incidents" value={kpis?.active_incidents ?? "—"} />
        <Kpi label="Traffic Index" value={kpis ? `${kpis.traffic_index}%` : "—"} accent="text-amber-400" />
        <Kpi label="Hospital Occupancy" value={kpis ? `${kpis.hospital_occupancy_pct}%` : "—"} accent="text-pink-400" />
        <Kpi label="Avg Response Time" value={kpis ? `${kpis.avg_response_time_min} min` : "—"} accent="text-sky-400" />
      </div>

      {/* Traffic by hour — simple bar chart */}
      <div className="rounded-xl border border-line bg-surface p-5">
        <div className="mb-4 flex items-center gap-2"><BarChart3 size={15} className="text-brand" /><h2 className="text-sm font-semibold text-ink">Traffic Index by Hour</h2></div>
        <div className="flex items-end gap-1 h-32">
          {trafficTrend.map((t) => (
            <div key={t.hour} className="flex flex-1 flex-col items-center gap-1">
              <div
                className="w-full rounded-t bg-brand/70 hover:bg-brand transition-all"
                style={{ height: `${(t.index / maxTraffic) * 100}%` }}
                title={`${t.hour}: ${t.index}`}
              />
              <span className="text-[9px] text-ink-faint">{t.hour.replace(":00", "")}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Incident severity distribution */}
      <div className="rounded-xl border border-line bg-surface p-5">
        <div className="mb-4 flex items-center gap-2"><TrendingUp size={15} className="text-brand" /><h2 className="text-sm font-semibold text-ink">Incident Severity Distribution</h2></div>
        <div className="space-y-3">
          {Object.entries(severityDist).map(([sev, count]) => {
            const total = Object.values(severityDist).reduce((s, v) => s + v, 0);
            const pct = Math.round(((count as number) / total) * 100);
            const color = sev === "CRITICAL" ? "bg-red-500" : sev === "HIGH" ? "bg-orange-400" : sev === "MEDIUM" ? "bg-amber-400" : "bg-emerald-400";
            return (
              <div key={sev}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-ink-muted">{sev}</span>
                  <span className="text-ink font-medium">{count as number} ({pct}%)</span>
                </div>
                <div className="h-2 w-full rounded-full bg-surface-muted">
                  <div className={`h-2 rounded-full ${color}`} style={{ width: `${pct}%` }} />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function Kpi({ label, value, accent = "text-ink" }: { label: string; value: string | number; accent?: string }) {
  return (
    <div className="rounded-xl border border-line bg-surface p-4">
      <p className="text-xs font-medium text-ink-muted">{label}</p>
      <p className={`mt-2 text-2xl font-bold tracking-tight ${accent}`}>{value}</p>
    </div>
  );
}
