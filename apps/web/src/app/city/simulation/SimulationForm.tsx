"use client";
import { useState, useTransition } from "react";
import { runSimulation } from "@/lib/city-api";
import type { SimulationScenario } from "@/lib/city-api";

export function SimulationForm() {
  const [pending, startTransition] = useTransition();
  const [result, setResult] = useState<SimulationScenario | null>(null);
  const [name, setName] = useState("Monsoon Road Closure Scenario");
  const [roadClosed, setRoadClosed] = useState(true);
  const [heavyRain, setHeavyRain] = useState(true);
  const [hospitalOverload, setHospitalOverload] = useState(false);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    startTransition(async () => {
      const scenario = await runSimulation({
        name,
        description: `Simulated: Road Closed=${roadClosed}, Heavy Rain=${heavyRain}, Hospital Overload=${hospitalOverload}`,
        parameters: {
          road_closed: roadClosed ? "Road 1024" : null,
          heavy_rain: heavyRain,
          hospital_overload: hospitalOverload,
          duration_hours: 24,
        },
      });
      setResult(scenario);
    });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-xs font-medium text-ink-muted mb-1">Scenario Name</label>
        <input
          id="sim-name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full rounded-lg border border-line bg-surface-muted px-3 py-2 text-sm text-ink placeholder-ink-faint focus:border-brand focus:outline-none"
        />
      </div>

      <div className="space-y-2">
        <p className="text-xs font-medium text-ink-muted">Scenario Parameters</p>
        <Toggle id="sim-road-closed" label="Close Road 1024" value={roadClosed} onChange={setRoadClosed} />
        <Toggle id="sim-heavy-rain" label="Heavy Rain Event (50mm/hr)" value={heavyRain} onChange={setHeavyRain} />
        <Toggle id="sim-hospital" label="Hospital Overload Condition" value={hospitalOverload} onChange={setHospitalOverload} />
      </div>

      <button
        id="sim-run-btn"
        type="submit"
        disabled={pending || !name}
        className="w-full rounded-lg bg-brand px-4 py-2.5 text-sm font-semibold text-brand-ink shadow-sm transition-all hover:bg-brand-strong disabled:opacity-50"
      >
        {pending ? "Running Simulation…" : "Run Simulation"}
      </button>

      {result && (
        <div className="mt-4 rounded-xl border border-emerald-500/30 bg-emerald-500/5 p-4">
          <p className="text-xs font-semibold text-emerald-400 mb-2">Simulation Results</p>
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(result.results).map(([k, v]) => (
              <div key={k} className="rounded bg-surface p-2">
                <p className="text-[10px] text-ink-faint capitalize">{k.replace(/_/g, " ")}</p>
                <p className="text-xs font-semibold text-ink">{String(v)}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </form>
  );
}

function Toggle({ id, label, value, onChange }: { id: string; label: string; value: boolean; onChange: (v: boolean) => void }) {
  return (
    <label htmlFor={id} className="flex cursor-pointer items-center justify-between rounded-lg border border-line bg-surface-muted/60 px-3 py-2">
      <span className="text-sm text-ink">{label}</span>
      <button
        id={id}
        type="button"
        role="switch"
        aria-checked={value}
        onClick={() => onChange(!value)}
        className={`relative inline-flex h-5 w-9 flex-shrink-0 rounded-full border-2 border-transparent transition-colors focus:outline-none ${value ? "bg-brand" : "bg-surface-muted"}`}
      >
        <span
          className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${value ? "translate-x-4" : "translate-x-0"}`}
        />
      </button>
    </label>
  );
}
