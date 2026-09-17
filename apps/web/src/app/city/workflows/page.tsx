import { getWorkflows } from "@/lib/city-api";
import { statusColor, severityColor } from "@/lib/colors";
import { Globe, Clock } from "lucide-react";

export const metadata = { title: "Workflows | CityOS", description: "Cross-department task management, SLA tracking, and approvals." };

export default async function WorkflowsPage() {
  const tasks = (await getWorkflows()) ?? [];
  return (
    <div className="min-h-screen p-6 space-y-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-widest text-brand">Government Workflow Engine</p>
        <h1 className="mt-1 text-2xl font-bold text-ink">Workflows & Task Management</h1>
        <p className="mt-1 text-sm text-ink-muted">Cross-department task assignment, approvals, SLA tracking, and escalation</p>
      </div>
      <div className="rounded-xl border border-line bg-surface p-5">
        <div className="mb-4 flex items-center gap-2"><Globe size={15} className="text-brand" /><h2 className="text-sm font-semibold text-ink">Active Tasks</h2></div>
        <div className="space-y-2">
          {tasks.map((t) => (
            <div key={t.id} className="flex flex-wrap items-center gap-3 rounded-lg bg-surface-muted/60 px-4 py-3">
              <span className={`rounded-full border px-2 py-0.5 text-[10px] font-bold ${severityColor(t.priority)}`}>{t.priority}</span>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-ink truncate">{t.title}</p>
                <p className="text-[10px] text-ink-faint">{t.task_number} · {t.department_code} · {t.assigned_to ?? "Unassigned"}</p>
              </div>
              <span className={`rounded-full border px-2 py-0.5 text-[10px] font-medium ${statusColor(t.status)}`}>{t.status}</span>
              {t.sla_deadline && <span className="flex items-center gap-1 text-[10px] text-ink-faint"><Clock size={10} />{new Date(t.sla_deadline).toLocaleDateString()}</span>}
            </div>
          ))}
          {tasks.length === 0 && <p className="text-center py-8 text-sm text-ink-faint">No workflow tasks found</p>}
        </div>
      </div>
    </div>
  );
}
