import { getIncidents } from "@/lib/city-api";
import { statusColor, severityColor } from "@/lib/colors";
import { Flame } from "lucide-react";

export const metadata = { title: "Emergency Operations | CityOS", description: "Emergency command center, dispatch, and incident response." };

export default async function EmergencyPage() {
  const res = await getIncidents(1);
  const incidents = res?.items ?? [];
  const active = incidents.filter(i => !["RESOLVED", "ANALYZED"].includes(i.status));
  const critical = incidents.filter(i => i.severity === "CRITICAL");

  return (
    <div className="min-h-screen p-6 space-y-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-widest text-brand">Emergency Department</p>
        <h1 className="mt-1 text-2xl font-bold text-ink">Emergency Operations Center</h1>
        <p className="mt-1 text-sm text-ink-muted">Live incident dispatch, ambulance coordination, and emergency response</p>
      </div>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Kpi label="Active Incidents" value={active.length} accent="text-red-400" />
        <Kpi label="Critical" value={critical.length} accent="text-orange-400" />
        <Kpi label="Total" value={incidents.length} />
        <Kpi label="Resolved" value={incidents.filter(i => i.status === "RESOLVED").length} accent="text-emerald-400" />
      </div>
      <div className="rounded-xl border border-line bg-surface p-5">
        <div className="mb-4 flex items-center gap-2"><Flame size={15} className="text-brand" /><h2 className="text-sm font-semibold text-ink">Active Responses</h2></div>
        <div className="space-y-2">
          {active.map((inc) => (
            <div key={inc.id} className="flex flex-wrap items-center gap-3 rounded-lg bg-surface-muted/60 px-4 py-3">
              <span className={`rounded-full border px-2 py-0.5 text-[10px] font-bold ${severityColor(inc.severity)}`}>{inc.severity}</span>
              <div className="flex-1 min-w-0"><p className="text-xs font-medium text-ink truncate">{inc.incident_number}</p><p className="text-[10px] text-ink-faint">{inc.incident_type.replace(/_/g, " ")}</p></div>
              <span className={`rounded-full border px-2 py-0.5 text-[10px] font-medium ${statusColor(inc.status)}`}>{inc.status}</span>
            </div>
          ))}
          {active.length === 0 && <p className="text-center py-8 text-sm text-ink-faint">No active emergencies</p>}
        </div>
      </div>
    </div>
  );
}
function Kpi({ label, value, accent = "text-ink" }: { label: string; value: number; accent?: string }) {
  return <div className="rounded-xl border border-line bg-surface p-4"><p className="text-xs font-medium text-ink-muted">{label}</p><p className={`mt-2 text-2xl font-bold tracking-tight ${accent}`}>{value}</p></div>;
}
