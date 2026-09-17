import { getKnowledge } from "@/lib/city-api";
import { AISupervisorPanel } from "@/components/AISupervisorPanel";
import { Brain, BookOpen, Tag } from "lucide-react";

export const metadata = {
  title: "AI Supervisor | CityOS",
  description: "Multi-agent AI city supervisor — anomaly detection, cascading risk analysis, and RAG knowledge retrieval.",
};

export default async function AIPage() {
  const docs = (await getKnowledge()) ?? [];

  return (
    <div className="min-h-screen p-6 space-y-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-widest text-brand">Intelligence Layer</p>
        <h1 className="mt-1 text-2xl font-bold text-ink">AI City Supervisor</h1>
        <p className="mt-1 text-sm text-ink-muted">
          Multi-agent analysis · Cascading risk detection · RAG knowledge retrieval
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* AI Supervisor Query Panel */}
        <div className="rounded-xl border border-line bg-surface p-5">
          <div className="mb-4 flex items-center gap-2">
            <Brain size={16} className="text-brand" />
            <h2 className="text-sm font-semibold text-ink">City Intelligence Query</h2>
          </div>
          <AISupervisorPanel />
        </div>

        {/* Agent Status */}
        <div className="space-y-4">
          <div className="rounded-xl border border-line bg-surface p-5">
            <h2 className="mb-3 text-sm font-semibold text-ink">Active Agents</h2>
            <div className="grid grid-cols-2 gap-2">
              {[
                { name: "Traffic Agent", status: "ACTIVE" },
                { name: "Emergency Agent", status: "ACTIVE" },
                { name: "Health Agent", status: "ACTIVE" },
                { name: "Utility Agent", status: "ACTIVE" },
                { name: "Risk Agent", status: "ACTIVE" },
                { name: "Knowledge Agent", status: "ACTIVE" },
                { name: "Report Agent", status: "STANDBY" },
                { name: "Supervisor Agent", status: "ACTIVE" },
              ].map((agent) => (
                <div key={agent.name} className="flex items-center gap-2 rounded-lg bg-surface-muted/60 px-3 py-2">
                  <span className={`h-1.5 w-1.5 rounded-full ${agent.status === "ACTIVE" ? "bg-emerald-400 animate-pulse" : "bg-ink-faint"}`} />
                  <span className="text-xs text-ink">{agent.name}</span>
                </div>
              ))}
            </div>
          </div>

          {/* RAG Knowledge Base */}
          <div className="rounded-xl border border-line bg-surface p-5">
            <div className="mb-3 flex items-center gap-2">
              <BookOpen size={14} className="text-brand" />
              <h2 className="text-sm font-semibold text-ink">Knowledge Base</h2>
            </div>
            <div className="space-y-2">
              {docs.map((doc) => (
                <div key={doc.id} className="rounded-lg bg-surface-muted/60 p-3">
                  <p className="text-xs font-semibold text-ink">{doc.title}</p>
                  <p className="mt-0.5 text-[10px] text-ink-muted line-clamp-2">{doc.content}</p>
                  <div className="mt-1.5 flex flex-wrap gap-1">
                    {doc.tags.map((tag) => (
                      <span key={tag} className="flex items-center gap-1 rounded-full bg-brand/10 px-1.5 py-0.5 text-[9px] font-medium text-brand">
                        <Tag size={8} />
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
              {docs.length === 0 && (
                <p className="text-center text-xs text-ink-faint py-4">No documents in knowledge base yet</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
