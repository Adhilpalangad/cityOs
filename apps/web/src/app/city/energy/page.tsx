import { getPowerSubstations } from "@/lib/city-api";
import { statusColor, severityColor } from "@/lib/colors";
import { Zap } from "lucide-react";

export const metadata = { title: "Energy Management | CityOS", description: "Power grid, substation load, and outage risk." };

export default async function EnergyPage() {
  const substations = (await getPowerSubstations()) ?? [];
  const totalCapacity = substations.reduce((s, p) => s + p.capacity_mw, 0);
  const totalLoad = substations.reduce((s, p) => s + p.load_mw, 0);
  const loadPct = Math.round((totalLoad / Math.max(totalCapacity, 1)) * 100);

  return (
    <div className="min-h-screen p-6 space-y-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-widest text-brand">Utilities</p>
        <h1 className="mt-1 text-2xl font-bold text-ink">Energy Management</h1>
        <p className="mt-1 text-sm text-ink-muted">Power grid substations, load distribution, and outage risk</p>
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Kpi label="Substations" value={substations.length} />
        <Kpi label="Total Capacity" value={`${totalCapacity} MW`} accent="text-yellow-400" />
        <Kpi label="Current Load" value={`${totalLoad.toFixed(0)} MW`} accent="text-amber-400" />
        <Kpi label="Grid Usage" value={`${loadPct}%`} accent={loadPct > 85 ? "text-red-400" : "text-emerald-400"} />
      </div>

      <div className="rounded-xl border border-line bg-surface p-5">
        <div className="mb-4 flex items-center gap-2"><Zap size={15} className="text-brand" /><h2 className="text-sm font-semibold text-ink">Substation Status</h2></div>
        <div className="space-y-3">
          {substations.map((ps) => {
            const pct = Math.round((ps.load_mw / Math.max(ps.capacity_mw, 1)) * 100);
            return (
              <div key={ps.id} className="rounded-lg bg-surface-muted/60 p-4">
                <div className="flex items-center justify-between mb-3">
                  <div><p className="text-sm font-semibold text-ink">{ps.name}</p><p className="text-xs text-ink-faint">{ps.substation_code}</p></div>
                  <div className="flex gap-2">
                    <span className={`rounded-full border px-2 py-0.5 text-[10px] font-medium ${statusColor(ps.status)}`}>{ps.status}</span>
                    <span className={`rounded-full border px-2 py-0.5 text-[10px] font-medium ${severityColor(ps.outage_risk)}`}>{ps.outage_risk} risk</span>
                  </div>
                </div>
                <div className="flex justify-between text-[10px] text-ink-muted mb-1">
                  <span>Load: {ps.load_mw} MW / {ps.capacity_mw} MW</span>
                  <span>{pct}%</span>
                </div>
                <div className="h-2 w-full rounded-full bg-surface-muted">
                  <div className={`h-2 rounded-full transition-all ${pct > 85 ? "bg-red-500" : pct > 70 ? "bg-amber-400" : "bg-brand"}`} style={{ width: `${pct}%` }} />
                </div>
              </div>
            );
          })}
          {substations.length === 0 && <p className="text-center py-8 text-sm text-ink-faint">No substation data</p>}
        </div>
      </div>
    </div>
  );
}

function Kpi({ label, value, accent = "text-ink" }: { label: string; value: string | number; accent?: string }) {
  return <div className="rounded-xl border border-line bg-surface p-4"><p className="text-xs font-medium text-ink-muted">{label}</p><p className={`mt-2 text-2xl font-bold tracking-tight ${accent}`}>{value}</p></div>;
}
