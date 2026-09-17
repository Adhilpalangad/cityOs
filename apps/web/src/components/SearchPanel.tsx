"use client";
import { useState, useTransition } from "react";
import { universalSearch } from "@/lib/city-api";
import type { UniversalSearchResult } from "@/lib/city-api";
import { Search, Loader2, MapPin, AlertTriangle, Hospital, Car } from "lucide-react";

export function SearchPanel() {
  const [pending, startTransition] = useTransition();
  const [q, setQ] = useState("");
  const [result, setResult] = useState<UniversalSearchResult | null>(null);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!q.trim()) return;
    startTransition(async () => {
      const res = await universalSearch(q.trim());
      setResult(res);
    });
  }

  const totalResults = result
    ? Object.values(result.results).reduce((s, arr) => s + arr.length, 0)
    : 0;

  return (
    <div className="space-y-4">
      <form onSubmit={handleSearch} className="flex gap-2">
        <div className="relative flex-1">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-faint" />
          <input
            id="universal-search-input"
            type="search"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search roads, hospitals, incidents, complaints…"
            className="w-full rounded-lg border border-line bg-surface-muted py-2.5 pl-9 pr-3 text-sm text-ink placeholder-ink-faint focus:border-brand focus:outline-none"
          />
        </div>
        <button
          id="universal-search-btn"
          type="submit"
          disabled={pending || !q.trim()}
          className="flex items-center gap-2 rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-brand-ink hover:bg-brand-strong disabled:opacity-50 transition-colors"
        >
          {pending ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />}
          {pending ? "Searching…" : "Search"}
        </button>
      </form>

      {result && (
        <div className="space-y-4">
          <p className="text-xs text-ink-muted">
            {totalResults} results for <span className="font-semibold text-ink">&ldquo;{result.query}&rdquo;</span>
          </p>

          {result.results.roads.length > 0 && (
            <ResultGroup title="Roads" icon={<MapPin size={13} className="text-amber-400" />}>
              {result.results.roads.map((r) => (
                <ResultItem key={r.id} primary={r.name} secondary={r.code} badge={r.status} />
              ))}
            </ResultGroup>
          )}
          {result.results.hospitals.length > 0 && (
            <ResultGroup title="Hospitals" icon={<Hospital size={13} className="text-pink-400" />}>
              {result.results.hospitals.map((h) => (
                <ResultItem key={h.id} primary={h.name} secondary={h.code} badge={`${h.beds_total} beds`} />
              ))}
            </ResultGroup>
          )}
          {result.results.incidents.length > 0 && (
            <ResultGroup title="Incidents" icon={<AlertTriangle size={13} className="text-red-400" />}>
              {result.results.incidents.map((i) => (
                <ResultItem key={i.id} primary={i.number} secondary={i.severity} badge={i.status} />
              ))}
            </ResultGroup>
          )}
          {result.results.complaints.length > 0 && (
            <ResultGroup title="Complaints" icon={<Car size={13} className="text-sky-400" />}>
              {result.results.complaints.map((c) => (
                <ResultItem key={c.id} primary={c.title} secondary={c.number} badge={c.status} />
              ))}
            </ResultGroup>
          )}

          {totalResults === 0 && (
            <div className="flex h-20 items-center justify-center text-sm text-ink-faint">
              No results found — try different keywords
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ResultGroup({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div>
      <p className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold text-ink-muted">{icon}{title}</p>
      <div className="space-y-1">{children}</div>
    </div>
  );
}

function ResultItem({ primary, secondary, badge }: { primary: string; secondary: string; badge: string }) {
  return (
    <div className="flex items-center gap-3 rounded-lg bg-surface-muted/60 px-3 py-2">
      <div className="flex-1 min-w-0">
        <p className="truncate text-xs font-medium text-ink">{primary}</p>
        <p className="text-[10px] text-ink-faint">{secondary}</p>
      </div>
      <span className="shrink-0 rounded-full bg-surface px-2 py-0.5 text-[10px] text-ink-muted border border-line">{badge}</span>
    </div>
  );
}
