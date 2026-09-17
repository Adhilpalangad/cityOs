"use client";
import { useState, useTransition } from "react";
import { analyzeCity } from "@/lib/city-api";
import type { AIAnalysis } from "@/lib/city-api";
import { Brain, Loader2, AlertCircle, CheckCircle, TrendingUp } from "lucide-react";

export function AISupervisorPanel() {
  const [pending, startTransition] = useTransition();
  const [query, setQuery] = useState("What are the current city risk factors?");
  const [result, setResult] = useState<AIAnalysis | null>(null);

  function handleAnalyze(e: React.FormEvent) {
    e.preventDefault();
    startTransition(async () => {
      const analysis = await analyzeCity(query);
      setResult(analysis);
    });
  }

  return (
    <div className="space-y-4">
      <form onSubmit={handleAnalyze} className="flex gap-2">
        <input
          id="ai-query"
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask the AI Supervisor…"
          className="flex-1 rounded-lg border border-line bg-surface-muted px-3 py-2 text-sm text-ink placeholder-ink-faint focus:border-brand focus:outline-none"
        />
        <button
          id="ai-analyze-btn"
          type="submit"
          disabled={pending || !query.trim()}
          className="flex items-center gap-2 rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-brand-ink hover:bg-brand-strong disabled:opacity-50 transition-colors"
        >
          {pending ? <Loader2 size={14} className="animate-spin" /> : <Brain size={14} />}
          {pending ? "Analyzing…" : "Analyze"}
        </button>
      </form>

      {result && (
        <div className="space-y-3">
          {/* Summary */}
          <div className="rounded-xl border border-brand/20 bg-brand/5 p-4">
            <p className="text-xs font-semibold text-brand mb-1">AI Summary</p>
            <p className="text-sm text-ink leading-relaxed">{result.summary}</p>
            <div className="mt-2 flex items-center gap-1 text-xs text-ink-muted">
              <TrendingUp size={11} />
              Confidence: {Math.round(result.confidence * 100)}%
            </div>
          </div>

          {/* Risks */}
          {result.risks_detected.length > 0 && (
            <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-4">
              <p className="text-xs font-semibold text-red-400 mb-2 flex items-center gap-1.5">
                <AlertCircle size={12} /> Risks Detected
              </p>
              <ul className="space-y-1">
                {result.risks_detected.map((r, i) => (
                  <li key={i} className="text-xs text-ink flex items-start gap-2">
                    <span className="mt-0.5 h-1.5 w-1.5 rounded-full bg-red-400 shrink-0" />
                    {r}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Recommendations */}
          {result.recommendations.length > 0 && (
            <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4">
              <p className="text-xs font-semibold text-emerald-400 mb-2 flex items-center gap-1.5">
                <CheckCircle size={12} /> Recommendations
              </p>
              <ul className="space-y-1.5">
                {result.recommendations.map((r, i) => (
                  <li key={i} className="text-xs text-ink flex items-start gap-2">
                    <span className="mt-0.5 h-1.5 w-1.5 rounded-full bg-emerald-400 shrink-0" />
                    {r}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Supporting data */}
          <div className="rounded-xl border border-line bg-surface-muted/60 p-4">
            <p className="text-xs font-semibold text-ink-muted mb-2">Supporting Data</p>
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(result.supporting_data).map(([k, v]) => (
                <div key={k} className="rounded bg-surface p-2">
                  <p className="text-[10px] text-ink-faint capitalize">{k.replace(/_/g, " ")}</p>
                  <p className="text-xs font-semibold text-ink mt-0.5">{String(v)}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
