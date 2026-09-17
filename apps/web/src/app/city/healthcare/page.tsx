import { getHospitals } from "@/lib/city-api";
import { statusColor, severityColor } from "@/lib/colors";
import { Bed, ActivitySquare } from "lucide-react";

export const metadata = {
  title: "Healthcare Network | CityOS",
  description: "Hospital capacity, ICU availability, emergency department load and ambulance fleet.",
};

export default async function HealthcarePage() {
  const res = await getHospitals();
  const hospitals = res?.items ?? [];

  const totalBeds = hospitals.reduce((s, h) => s + h.beds_total, 0);
  const totalOccupied = hospitals.reduce((s, h) => s + h.beds_occupied, 0);
  const totalICU = hospitals.reduce((s, h) => s + h.icu_total, 0);
  const totalICUOcc = hospitals.reduce((s, h) => s + h.icu_occupied, 0);
  const overloaded = hospitals.filter((h) => h.emergency_capacity === "HIGH" || h.emergency_capacity === "CRITICAL").length;

  return (
    <div className="min-h-screen p-6 space-y-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-widest text-brand">City Healthcare</p>
        <h1 className="mt-1 text-2xl font-bold text-ink">Healthcare Network</h1>
        <p className="mt-1 text-sm text-ink-muted">Real-time hospital capacity, ICU, and emergency department status</p>
      </div>

      {/* Summary KPIs */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <KpiCard label="Total Beds" value={totalBeds} sub={`${totalOccupied} occupied`} color="text-sky-400" />
        <KpiCard label="ICU Capacity" value={totalICU} sub={`${totalICUOcc} in use`} color="text-pink-400" />
        <KpiCard
          label="Bed Occupancy"
          value={`${Math.round((totalOccupied / Math.max(totalBeds, 1)) * 100)}%`}
          sub="Network average"
          color="text-violet-400"
        />
        <KpiCard
          label="Under Pressure"
          value={overloaded}
          sub="High/Critical load"
          color={overloaded > 0 ? "text-red-400" : "text-emerald-400"}
        />
      </div>

      {/* Hospital Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {hospitals.map((h) => {
          const bedPct = Math.round((h.beds_occupied / Math.max(h.beds_total, 1)) * 100);
          const icuPct = Math.round((h.icu_occupied / Math.max(h.icu_total, 1)) * 100);
          return (
            <div key={h.id} className="rounded-xl border border-line bg-surface p-5 hover:border-brand/30 transition-colors">
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-semibold text-ink">{h.name}</p>
                  <p className="text-xs text-ink-faint mt-0.5">{h.code}</p>
                </div>
                <span className={`rounded-full border px-2 py-0.5 text-[10px] font-medium ${statusColor(h.status)}`}>{h.status}</span>
              </div>
              <div className="mt-4 space-y-3">
                <div>
                  <div className="mb-1 flex justify-between text-xs">
                    <span className="text-ink-muted flex items-center gap-1"><Bed size={11} /> Beds</span>
                    <span className="text-ink font-medium">{h.beds_occupied} / {h.beds_total}</span>
                  </div>
                  <ProgressBar pct={bedPct} />
                </div>
                <div>
                  <div className="mb-1 flex justify-between text-xs">
                    <span className="text-ink-muted flex items-center gap-1"><ActivitySquare size={11} /> ICU</span>
                    <span className="text-ink font-medium">{h.icu_occupied} / {h.icu_total}</span>
                  </div>
                  <ProgressBar pct={icuPct} critical={icuPct > 85} />
                </div>
              </div>
              <div className="mt-4 flex items-center justify-between">
                <span className="text-xs text-ink-muted">Emergency</span>
                <span className={`rounded-full border px-2 py-0.5 text-[10px] font-bold ${severityColor(h.emergency_capacity)}`}>
                  {h.emergency_capacity}
                </span>
              </div>
            </div>
          );
        })}
        {hospitals.length === 0 && (
          <p className="col-span-full text-center text-sm text-ink-faint py-12">
            No hospitals found — seed data via the API
          </p>
        )}
      </div>
    </div>
  );
}

function KpiCard({ label, value, sub, color }: { label: string; value: string | number; sub: string; color: string }) {
  return (
    <div className="rounded-xl border border-line bg-surface p-4">
      <p className="text-xs font-medium text-ink-muted">{label}</p>
      <p className={`mt-2 text-2xl font-bold tracking-tight ${color}`}>{value}</p>
      <p className="mt-0.5 text-[11px] text-ink-faint">{sub}</p>
    </div>
  );
}

function ProgressBar({ pct, critical = false }: { pct: number; critical?: boolean }) {
  const color = critical ? "bg-red-500" : pct > 80 ? "bg-orange-400" : pct > 60 ? "bg-amber-400" : "bg-brand";
  return (
    <div className="h-2 w-full rounded-full bg-surface-muted">
      <div className={`h-2 rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
    </div>
  );
}
