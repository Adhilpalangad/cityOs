import { getIncidents } from "@/lib/city-api";
import { severityColor, statusColor } from "@/lib/colors";
import { AlertTriangle, Clock } from "lucide-react";

export const metadata = {
  title: "Incident Management | CityOS",
  description: "Track and manage city-wide incidents across all departments.",
};

export default async function IncidentsPage() {
  const incidentsRes = await getIncidents(1);
  const incidents = incidentsRes?.items ?? [];
  const meta = incidentsRes?.meta;

  const byStatus = incidents.reduce<Record<string, number>>((acc, i) => {
    acc[i.status] = (acc[i.status] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="min-h-screen p-6 space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-brand">Emergency Operations</p>
          <h1 className="mt-1 text-2xl font-bold text-ink">Incident Management</h1>
          <p className="mt-1 text-sm text-ink-muted">Full incident lifecycle — detection, assignment, response, resolution</p>
        </div>
        <div className="text-xs text-ink-muted border border-line rounded-lg px-3 py-2 flex gap-2 items-center">
          <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          {meta?.total ?? 0} total incidents
        </div>
      </div>

      {/* Status breakdown */}
      <div className="grid grid-cols-3 gap-3 sm:grid-cols-6">
        {["DETECTED", "VERIFIED", "ASSIGNED", "RESPONDING", "RESOLVED", "ANALYZED"].map((status) => (
          <div key={status} className="rounded-xl border border-line bg-surface p-3 text-center">
            <p className="text-xl font-bold text-ink">{byStatus[status] ?? 0}</p>
            <p className={`mt-1 text-[10px] font-semibold uppercase rounded-full border px-2 py-0.5 inline-block ${statusColor(status)}`}>
              {status}
            </p>
          </div>
        ))}
      </div>

      {/* Incidents Table */}
      <div className="rounded-xl border border-line bg-surface p-5">
        <h2 className="mb-4 text-sm font-semibold text-ink">All Incidents</h2>
        {incidents.length === 0 ? (
          <div className="flex h-32 flex-col items-center justify-center gap-2 text-sm text-ink-faint">
            <AlertTriangle size={24} className="opacity-40" />
            <p>No incidents yet. Create one via the API or wait for the data provider.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-line text-left text-ink-faint">
                  <th className="pb-2 pr-4 font-medium">Number</th>
                  <th className="pb-2 pr-4 font-medium">Type</th>
                  <th className="pb-2 pr-4 font-medium">Severity</th>
                  <th className="pb-2 pr-4 font-medium">Status</th>
                  <th className="pb-2 pr-4 font-medium">Department</th>
                  <th className="pb-2 font-medium">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line/50">
                {incidents.map((inc) => (
                  <tr key={inc.id} className="hover:bg-surface-muted/40 transition-colors">
                    <td className="py-2.5 pr-4 font-mono font-medium text-ink">{inc.incident_number}</td>
                    <td className="py-2.5 pr-4 text-ink-muted">{inc.incident_type.replace(/_/g, " ")}</td>
                    <td className="py-2.5 pr-4">
                      <span className={`rounded-full border px-2 py-0.5 text-[10px] font-bold ${severityColor(inc.severity)}`}>
                        {inc.severity}
                      </span>
                    </td>
                    <td className="py-2.5 pr-4">
                      <span className={`rounded-full border px-2 py-0.5 text-[10px] font-medium ${statusColor(inc.status)}`}>
                        {inc.status}
                      </span>
                    </td>
                    <td className="py-2.5 pr-4 text-ink-muted">{inc.department_code ?? "—"}</td>
                    <td className="py-2.5 text-ink-faint flex items-center gap-1">
                      <Clock size={10} />
                      {new Date(inc.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
