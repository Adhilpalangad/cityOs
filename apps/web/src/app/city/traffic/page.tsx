import { getRoads } from "@/lib/city-api";
import { statusColor, severityColor, trafficDotColor } from "@/lib/colors";

export const metadata = {
  title: "Traffic Intelligence | CityOS",
  description: "Live road traffic, congestion analysis, and road network status.",
};

export default async function TrafficPage() {
  const res = await getRoads();
  const roads = res?.items ?? [];
  const avgSpeed = roads.filter(r => r.average_speed_kmh).reduce((s, r) => s + (r.average_speed_kmh ?? 0), 0) / Math.max(roads.filter(r => r.average_speed_kmh).length, 1);
  const criticalRoads = roads.filter(r => r.traffic_level === "CRITICAL").length;
  const closedRoads = roads.filter(r => r.status === "CLOSED").length;

  return (
    <div className="min-h-screen p-6 space-y-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-widest text-brand">Traffic Department</p>
        <h1 className="mt-1 text-2xl font-bold text-ink">Traffic Intelligence</h1>
        <p className="mt-1 text-sm text-ink-muted">Live road conditions, vehicle counts, and congestion analysis</p>
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Kpi label="Roads Monitored" value={roads.length} />
        <Kpi label="Critical Congestion" value={criticalRoads} accent="text-red-400" />
        <Kpi label="Avg Speed" value={`${Math.round(avgSpeed)} km/h`} accent="text-amber-400" />
        <Kpi label="Roads Closed" value={closedRoads} accent={closedRoads > 0 ? "text-red-400" : "text-emerald-400"} />
      </div>

      <div className="rounded-xl border border-line bg-surface p-5">
        <h2 className="mb-4 text-sm font-semibold text-ink">Road Network Status</h2>
        <div className="space-y-2">
          {roads.map((r) => (
            <div key={r.id} className="flex flex-wrap items-center gap-3 rounded-lg bg-surface-muted/60 px-4 py-3">
              <span className={`h-2 w-2 rounded-full shrink-0 ${trafficDotColor(r.traffic_level)}`} />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-ink truncate">{r.name}</p>
                <p className="text-[10px] text-ink-faint">{r.code} · {r.road_type}</p>
              </div>
              <div className="flex items-center gap-2 text-xs text-ink-muted">
                <span>{r.current_vehicle_count} vehicles</span>
                {r.average_speed_kmh && <span>· {r.average_speed_kmh} km/h</span>}
              </div>
              <span className={`rounded-full border px-2 py-0.5 text-[10px] font-bold ${severityColor(r.traffic_level)}`}>{r.traffic_level}</span>
              <span className={`rounded-full border px-2 py-0.5 text-[10px] font-medium ${statusColor(r.status)}`}>{r.status}</span>
              <span className={`rounded-full border px-2 py-0.5 text-[10px] font-medium ${severityColor(r.risk_level)}`}>{r.risk_level} risk</span>
            </div>
          ))}
          {roads.length === 0 && (
            <p className="text-center py-8 text-sm text-ink-faint">No roads in database — add roads via the API</p>
          )}
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
