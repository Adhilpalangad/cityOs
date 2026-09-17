import { getEnvironmentReadings } from "@/lib/city-api";
import { severityColor } from "@/lib/colors";
import { Thermometer, Droplets, Wind, TreePine } from "lucide-react";

export const metadata = { title: "Environmental Intelligence | CityOS", description: "Weather, temperature, rainfall, AQI, and flood risk." };

export default async function EnvironmentPage() {
  const readings = (await getEnvironmentReadings()) ?? [];
  const highFloodRisk = readings.filter(r => r.flood_risk === "HIGH" || r.flood_risk === "CRITICAL").length;

  return (
    <div className="min-h-screen p-6 space-y-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-widest text-brand">Environmental Intelligence</p>
        <h1 className="mt-1 text-2xl font-bold text-ink">Environmental Monitoring</h1>
        <p className="mt-1 text-sm text-ink-muted">Weather, temperature, rainfall, air quality, and flood risk</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {readings.map((r) => (
          <div key={r.id} className="rounded-xl border border-line bg-surface p-5 hover:border-brand/30 transition-colors">
            <div className="flex items-center justify-between mb-3">
              <div><p className="text-sm font-semibold text-ink">{r.zone_code}</p></div>
              <span className={`rounded-full border px-2 py-0.5 text-[10px] font-bold ${severityColor(r.flood_risk)}`}>
                Flood: {r.flood_risk}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <ReadingItem icon={<Thermometer size={12} className="text-orange-400" />} label="Temperature" value={`${r.temperature_c}°C`} />
              <ReadingItem icon={<Droplets size={12} className="text-sky-400" />} label="Rainfall" value={`${r.rainfall_mm} mm`} />
              <ReadingItem icon={<Wind size={12} className="text-slate-400" />} label="Humidity" value={`${r.humidity_pct}%`} />
              <ReadingItem icon={<TreePine size={12} className="text-emerald-400" />} label="AQI" value={r.aqi.toString()} />
            </div>
          </div>
        ))}
        {readings.length === 0 && (
          <p className="col-span-full text-center py-8 text-sm text-ink-faint">No environment readings available</p>
        )}
      </div>

      {highFloodRisk > 0 && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/5 p-4 flex gap-3">
          <span className="text-red-400 text-lg">⚠️</span>
          <div>
            <p className="text-sm font-semibold text-red-400">Flood Risk Alert</p>
            <p className="text-xs text-ink-muted mt-0.5">{highFloodRisk} zone(s) at HIGH or CRITICAL flood risk. Emergency services have been notified.</p>
          </div>
        </div>
      )}
    </div>
  );
}

function ReadingItem({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="rounded-lg bg-surface-muted/60 p-2.5">
      <div className="flex items-center gap-1 mb-1">{icon}<span className="text-[10px] text-ink-faint">{label}</span></div>
      <p className="text-sm font-semibold text-ink">{value}</p>
    </div>
  );
}
