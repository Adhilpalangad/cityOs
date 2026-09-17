import { getAuditLogs } from "@/lib/city-api";
import { ShieldCheck, Clock } from "lucide-react";

export const metadata = { title: "Audit Log | CityOS", description: "Immutable audit trail of all sensitive city platform actions." };

export default async function AuditPage() {
  const logs = (await getAuditLogs()) ?? [];

  return (
    <div className="min-h-screen p-6 space-y-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-widest text-brand">Platform Security</p>
        <h1 className="mt-1 text-2xl font-bold text-ink">Audit Log</h1>
        <p className="mt-1 text-sm text-ink-muted">Append-only log of all sensitive actions and approvals</p>
      </div>

      <div className="rounded-xl border border-line bg-surface p-5">
        <div className="mb-4 flex items-center gap-2"><ShieldCheck size={15} className="text-brand" /><h2 className="text-sm font-semibold text-ink">Recent Actions</h2></div>
        <div className="space-y-2">
          {logs.map((l) => (
            <div key={l.id} className="rounded-lg bg-surface-muted/60 p-4">
              <div className="flex flex-wrap items-start gap-3">
                <code className="text-xs font-mono font-bold text-brand">{l.action}</code>
                <span className="text-xs text-ink-muted flex items-center gap-1"><Clock size={10} />{new Date(l.timestamp).toLocaleString()}</span>
              </div>
              <div className="mt-2 grid grid-cols-2 gap-2 text-xs sm:grid-cols-4">
                <div><p className="text-ink-faint">Actor</p><p className="text-ink font-medium">{l.actor}</p></div>
                <div><p className="text-ink-faint">Resource</p><p className="text-ink font-medium">{l.target_resource}</p></div>
                <div><p className="text-ink-faint">Department</p><p className="text-ink font-medium">{l.department_code ?? "—"}</p></div>
                <div><p className="text-ink-faint">Approved By</p><p className="text-ink font-medium">{l.approved_by ?? "—"}</p></div>
              </div>
              {l.reason && <p className="mt-2 text-xs text-ink-muted italic">{l.reason}</p>}
            </div>
          ))}
          {logs.length === 0 && <p className="text-center py-8 text-sm text-ink-faint">No audit logs found</p>}
        </div>
      </div>
    </div>
  );
}
