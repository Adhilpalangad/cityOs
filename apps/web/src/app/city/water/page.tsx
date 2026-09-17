import { getWaterZones } from "@/lib/city-api";
import { statusColor, severityColor } from "@/lib/colors";
import { Droplets } from "lucide-react";

export const metadata = { title: "Water Management | CityOS", description: "Water zone distribution, consumption, leak risk, and outage status." };

export default async function WaterPage() {
  const zones = (await getWaterZones()) ?? [];
  const totalCapacity = zones.reduce((s, z) => s + z.capacity_liters, 0);
  const totalConsumption = zones.reduce((s, z) => s + z.consumption_lps, 0);
  const highRisk = zones.filter(z => z.leak_risk === "HIGH" || z.leak_risk === "CRITICAL").length;

  return (
    <div className="min-h-screen p-6 space-y-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-widest text-brand">Utilities</p>
        <h1 className="mt-1 text-2xl font-bold text-ink">Water Management</h1>
        <p className="mt-1 text-sm text-ink-muted">Reservoirs, distribution zones, consumption, and leak risk</p>
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Kpi label="Distribution Zones" value={zones.length} />
        <Kpi label="Total Capacity" value={`${(totalCapacity / 1e6).toFixed(1)}M L`} accent="text-sky-400" />
        <Kpi label="Consumption" value={`${totalConsumption.toFixed(0)} L/s`} accent="text-blue-400" />
        <Kpi label="High Leak Risk" value={highRisk} accent={highRisk > 0 ? "text-red-400" : "text-emerald-400"} />
      </div>

      <div className="rounded-xl border border-line bg-surface p-5">
        <div className="mb-4 flex items-center gap-2"><Droplets size={15} className="text-brand" /><h2 className="text-sm font-semibold text-ink">Water Zone Status</h2></div>
        <div className="space-y-3">
          {zones.map((z) => (
            <div key={z.id} className="rounded-lg bg-surface-muted/60 p-4">
              <div className="flex items-center justify-between">
                <div><p className="text-sm font-semibold text-ink">{z.name}</p><p className="text-xs text-ink-faint">{z.zone_code}</p></div>
                <div className="flex gap-2">
                  <span className={`rounded-full border px-2 py-0.5 text-[10px] font-medium ${statusColor(z.status)}`}>{z.status}</span>
                  <span className={`rounded-full border px-2 py-0.5 text-[10px] font-medium ${severityColor(z.leak_risk)}`}>{z.leak_risk} risk</span>
                </div>
              </div>
              <div className="mt-3 grid grid-cols-3 gap-3 text-xs">
                <div><p className="text-ink-faint">Capacity</p><p className="font-medium text-ink">{(z.capacity_liters / 1e6).toFixed(2)}M L</p></div>
                <div><p className="text-ink-faint">Consumption</p><p className="font-medium text-ink">{z.consumption_lps} L/s</p></div>
                <div><p className="text-ink-faint">Active Outages</p><p className={`font-medium ${z.outages_active > 0 ? "text-red-400" : "text-emerald-400"}`}>{z.outages_active}</p></div>
              </div>
            </div>
          ))}
          {zones.length === 0 && <p className="text-center py-8 text-sm text-ink-faint">No water zones data</p>}
        </div>
      </div>
    </div>
  );
}

function Kpi({ label, value, accent = "text-ink" }: { label: string; value: string | number; accent?: string }) {
  return <div className="rounded-xl border border-line bg-surface p-4"><p className="text-xs font-medium text-ink-muted">{label}</p><p className={`mt-2 text-2xl font-bold tracking-tight ${accent}`}>{value}</p></div>;
}
