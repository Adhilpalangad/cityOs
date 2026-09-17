import { SearchPanel } from "@/components/SearchPanel";

export const metadata = {
  title: "Universal Search | CityOS",
  description: "Search across all city entities — roads, hospitals, incidents, complaints, and knowledge.",
};

export default function SearchPage() {
  return (
    <div className="min-h-screen p-6 space-y-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-widest text-brand">City Intelligence</p>
        <h1 className="mt-1 text-2xl font-bold text-ink">Universal City Search</h1>
        <p className="mt-1 text-sm text-ink-muted">
          Search roads, hospitals, incidents, complaints, and city knowledge base in one place
        </p>
      </div>
      <div className="rounded-xl border border-line bg-surface p-6">
        <SearchPanel />
      </div>

      {/* Search tips */}
      <div className="rounded-xl border border-line bg-surface p-5">
        <h2 className="mb-3 text-sm font-semibold text-ink">Search Tips</h2>
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {[
            { tip: "hospital", desc: "Find hospitals by name or code" },
            { tip: "INC-", desc: "Search by incident number prefix" },
            { tip: "pothole", desc: "Find citizen complaints by keyword" },
            { tip: "metro", desc: "Find metro roads or routes" },
            { tip: "CMP-", desc: "Search by complaint number" },
            { tip: "H-01", desc: "Find hospital by code" },
          ].map(({ tip, desc }) => (
            <div key={tip} className="rounded-lg bg-surface-muted/60 p-3">
              <code className="text-xs font-mono text-brand">{tip}</code>
              <p className="mt-0.5 text-[11px] text-ink-muted">{desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
