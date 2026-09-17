import { getTransitRoutes, getBusStops } from "@/lib/city-api";
import { statusColor } from "@/lib/colors";
import { Bus, MapPin } from "lucide-react";

export const metadata = {
  title: "Public Transport | CityOS",
  description: "Transit fleet, routes, stops, schedules, and passenger demand.",
};

export default async function TransportPage() {
  const [routes, stops] = await Promise.all([getTransitRoutes(), getBusStops()]);

  return (
    <div className="min-h-screen p-6 space-y-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-widest text-brand">Transport Department</p>
        <h1 className="mt-1 text-2xl font-bold text-ink">Public Transport</h1>
        <p className="mt-1 text-sm text-ink-muted">Routes, bus stops, fleet status, and passenger demand</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-line bg-surface p-5">
          <div className="mb-4 flex items-center gap-2">
            <Bus size={15} className="text-brand" />
            <h2 className="text-sm font-semibold text-ink">Active Routes</h2>
          </div>
          <div className="space-y-3">
            {(routes ?? []).map((r) => (
              <div key={r.id} className="rounded-lg bg-surface-muted/60 p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold text-ink">{r.name}</p>
                    <p className="text-xs text-ink-muted">{r.route_number}</p>
                  </div>
                  <span className={`rounded-full border px-2 py-0.5 text-[10px] font-medium ${statusColor(r.status)}`}>{r.status}</span>
                </div>
                <div className="mt-2 flex items-center gap-1 text-xs text-ink-muted">
                  <MapPin size={10} className="shrink-0" />{r.origin}
                  <span className="mx-1">→</span>
                  {r.destination}
                </div>
                <div className="mt-2 flex gap-4 text-xs">
                  <span className="text-ink-muted">{r.distance_km} km</span>
                  <span className="text-ink-muted">{r.active_buses} buses active</span>
                </div>
              </div>
            ))}
            {(routes?.length ?? 0) === 0 && (
              <p className="text-center py-6 text-sm text-ink-faint">No routes data</p>
            )}
          </div>
        </div>

        <div className="rounded-xl border border-line bg-surface p-5">
          <div className="mb-4 flex items-center gap-2">
            <MapPin size={15} className="text-brand" />
            <h2 className="text-sm font-semibold text-ink">Bus Stops</h2>
          </div>
          <div className="space-y-2">
            {(stops ?? []).map((s) => (
              <div key={s.id} className="flex items-center gap-3 rounded-lg bg-surface-muted/60 px-3 py-2.5">
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-ink truncate">{s.name}</p>
                  <p className="text-[10px] text-ink-faint">{s.code} · Route: {s.route_code ?? "—"}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-ink">{s.passenger_count}</p>
                  <p className="text-[10px] text-ink-faint">passengers</p>
                </div>
              </div>
            ))}
            {(stops?.length ?? 0) === 0 && (
              <p className="text-center py-6 text-sm text-ink-faint">No stops data</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
