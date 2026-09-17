import { getSimulations } from "@/lib/city-api";
import { SimulationForm } from "./SimulationForm";
import { FlaskConical } from "lucide-react";

export const metadata = {
  title: "Simulation Lab | CityOS",
  description: "Run what-if scenario simulations to predict city-wide impacts of events and interventions.",
};

export default async function SimulationPage() {
  const scenarios = (await getSimulations()) ?? [];

  return (
    <div className="min-h-screen p-6 space-y-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-widest text-brand">What-If Engine</p>
        <h1 className="mt-1 text-2xl font-bold text-ink">Simulation Lab</h1>
        <p className="mt-1 text-sm text-ink-muted">
          Build city scenarios, run impact models, and compare interventions
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Scenario Builder */}
        <div className="rounded-xl border border-line bg-surface p-5">
          <div className="mb-4 flex items-center gap-2">
            <FlaskConical size={16} className="text-brand" />
            <h2 className="text-sm font-semibold text-ink">Create Scenario</h2>
          </div>
          <SimulationForm />
        </div>

        {/* Past Scenarios */}
        <div className="rounded-xl border border-line bg-surface p-5">
          <h2 className="mb-4 text-sm font-semibold text-ink">Scenario History</h2>
          <div className="space-y-3">
            {scenarios.map((s) => (
              <div key={s.id} className="rounded-lg border border-line bg-surface-muted/60 p-4">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="text-sm font-semibold text-ink">{s.name}</p>
                    <p className="text-xs text-ink-muted mt-0.5">{s.description ?? s.scenario_code}</p>
                  </div>
                  <span className="shrink-0 rounded-full border border-line bg-surface-muted px-2 py-0.5 text-[10px] font-medium text-ink-muted">
                    {s.status}
                  </span>
                </div>
                {Object.keys(s.results).length > 0 && (
                  <div className="mt-3 grid grid-cols-2 gap-2">
                    {Object.entries(s.results).slice(0, 4).map(([k, v]) => (
                      <div key={k} className="rounded bg-surface p-2">
                        <p className="text-[10px] text-ink-faint capitalize">{k.replace(/_/g, " ")}</p>
                        <p className="text-xs font-semibold text-ink mt-0.5">{String(v)}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {scenarios.length === 0 && (
              <div className="flex h-24 items-center justify-center text-sm text-ink-faint">
                No scenarios yet — create one!
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
