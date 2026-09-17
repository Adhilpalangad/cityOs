import { getInfrastructureAssets, getCityProjects } from "@/lib/city-api";
import { statusColor, severityColor } from "@/lib/colors";
import { Wrench, FolderOpen } from "lucide-react";

export const metadata = { title: "Infrastructure Management | CityOS", description: "Asset tracking, maintenance schedules, risk levels and city projects." };

export default async function InfrastructurePage() {
  const [assets, projects] = await Promise.all([getInfrastructureAssets(), getCityProjects()]);

  return (
    <div className="min-h-screen p-6 space-y-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-widest text-brand">Infrastructure Department</p>
        <h1 className="mt-1 text-2xl font-bold text-ink">Infrastructure Management</h1>
        <p className="mt-1 text-sm text-ink-muted">Asset registry, condition tracking, and city development projects</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Assets */}
        <div className="rounded-xl border border-line bg-surface p-5">
          <div className="mb-4 flex items-center gap-2"><Wrench size={15} className="text-brand" /><h2 className="text-sm font-semibold text-ink">Infrastructure Assets</h2></div>
          <div className="space-y-2">
            {(assets ?? []).map((a) => (
              <div key={a.id} className="flex flex-wrap items-center gap-3 rounded-lg bg-surface-muted/60 px-3 py-2.5">
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-ink truncate">{a.name}</p>
                  <p className="text-[10px] text-ink-faint">{a.asset_code} · {a.asset_type}</p>
                </div>
                <span className={`rounded-full border px-2 py-0.5 text-[10px] font-medium ${statusColor(a.condition)}`}>{a.condition}</span>
                <span className={`rounded-full border px-2 py-0.5 text-[10px] font-medium ${severityColor(a.risk_level)}`}>{a.risk_level} risk</span>
              </div>
            ))}
            {(assets?.length ?? 0) === 0 && <p className="text-center py-8 text-sm text-ink-faint">No assets registered</p>}
          </div>
        </div>

        {/* Projects */}
        <div className="rounded-xl border border-line bg-surface p-5">
          <div className="mb-4 flex items-center gap-2"><FolderOpen size={15} className="text-brand" /><h2 className="text-sm font-semibold text-ink">City Projects & Finance</h2></div>
          <div className="space-y-3">
            {(projects ?? []).map((p) => {
              const variantPct = Math.round((p.spent / Math.max(p.budget, 1)) * 100);
              return (
                <div key={p.id} className="rounded-lg bg-surface-muted/60 p-4">
                  <div className="flex items-start justify-between gap-2">
                    <div><p className="text-xs font-semibold text-ink">{p.name}</p><p className="text-[10px] text-ink-faint">{p.project_code} · {p.department_code}</p></div>
                    <span className={`shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-medium ${statusColor(p.status)}`}>{p.status}</span>
                  </div>
                  <div className="mt-2 flex justify-between text-[10px] text-ink-muted">
                    <span>Budget: ₹{(p.budget / 1e5).toFixed(1)}L</span>
                    <span>Spent: ₹{(p.spent / 1e5).toFixed(1)}L ({variantPct}%)</span>
                  </div>
                  <div className="mt-1.5 h-2 w-full rounded-full bg-surface-muted">
                    <div className={`h-2 rounded-full transition-all ${p.completion_percentage > 80 ? "bg-emerald-400" : "bg-brand"}`} style={{ width: `${p.completion_percentage}%` }} />
                  </div>
                  <p className="mt-1 text-[10px] text-ink-faint text-right">{p.completion_percentage}% complete</p>
                </div>
              );
            })}
            {(projects?.length ?? 0) === 0 && <p className="text-center py-8 text-sm text-ink-faint">No projects found</p>}
          </div>
        </div>
      </div>
    </div>
  );
}
