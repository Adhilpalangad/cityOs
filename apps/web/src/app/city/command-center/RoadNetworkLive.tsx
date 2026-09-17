"use client";

import type { Road } from "@/lib/city-api";
import { severityColor, statusColor } from "@/lib/colors";
import { useLiveFeed } from "@/lib/live-socket";

/**
 * Renders the Road Network Status table from the page's initial
 * server-fetched snapshot, then layers live updates from the traffic
 * provider on top (see docs/architecture.md's "Phase 3" note) as they
 * arrive over `useLiveFeed()` -- no polling, no page refresh.
 */
export function RoadNetworkLive({ initialRoads }: { initialRoads: Road[] }) {
  const { roads: liveRoads, connected } = useLiveFeed();

  const roads = initialRoads.map((road) => liveRoads[road.code] ?? road);
  for (const [code, road] of Object.entries(liveRoads)) {
    if (!roads.some((r) => r.code === code)) roads.push(road);
  }

  return (
    <div className="rounded-xl border border-line bg-surface p-5">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-ink">Road Network Status</h2>
        <span
          className={`flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[10px] font-medium ${
            connected
              ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-400"
              : "border-line text-ink-faint"
          }`}
        >
          <span className={`h-1.5 w-1.5 rounded-full ${connected ? "bg-emerald-400 animate-pulse" : "bg-ink-faint"}`} />
          {connected ? "Live" : "Connecting…"}
        </span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-line text-left text-ink-faint">
              <th className="pb-2 pr-4 font-medium">Road</th>
              <th className="pb-2 pr-4 font-medium">Status</th>
              <th className="pb-2 pr-4 font-medium">Traffic</th>
              <th className="pb-2 pr-4 font-medium">Vehicles</th>
              <th className="pb-2 font-medium">Risk</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line/50">
            {roads.map((r) => (
              <tr key={r.id ?? r.code}>
                <td className="py-2 pr-4 font-medium text-ink">{r.name}</td>
                <td className="py-2 pr-4">
                  <span className={`rounded-full border px-2 py-0.5 text-[10px] font-medium ${statusColor(r.status)}`}>{r.status}</span>
                </td>
                <td className="py-2 pr-4">
                  <span className={`rounded-full border px-2 py-0.5 text-[10px] font-bold ${severityColor(r.traffic_level)}`}>{r.traffic_level}</span>
                </td>
                <td className="py-2 pr-4 text-ink-muted">{r.current_vehicle_count} / {r.capacity}</td>
                <td className="py-2">
                  <span className={`rounded-full border px-2 py-0.5 text-[10px] font-medium ${severityColor(r.risk_level)}`}>{r.risk_level}</span>
                </td>
              </tr>
            ))}
            {roads.length === 0 && (
              <tr>
                <td colSpan={5} className="py-6 text-center text-ink-faint">
                  No roads in the database yet
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
