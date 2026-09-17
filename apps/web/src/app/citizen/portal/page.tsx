import Link from "next/link";
import { getComplaints, getNotifications } from "@/lib/city-api";
import { statusColor, severityColor } from "@/lib/colors";
import { Users, MessageSquarePlus, Bell } from "lucide-react";

export const metadata = {
  title: "Citizen Portal | CityOS",
  description: "Report issues, track complaints, receive alerts and access city services.",
};

export default async function CitizenPortalPage() {
  const [complaints, notifications] = await Promise.all([getComplaints(), getNotifications()]);

  return (
    <div className="min-h-screen bg-[#060b14]">
      {/* Portal header */}
      <div className="border-b border-line bg-surface/80 px-6 py-4 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand text-brand-ink font-black text-sm">C</span>
            <span className="font-bold text-ink">CityOS Citizen Portal</span>
          </div>
          <Link href="/city/command-center" className="text-xs text-ink-muted hover:text-brand transition-colors">
            → Admin Dashboard
          </Link>
        </div>
      </div>

      <div className="mx-auto max-w-5xl px-6 py-8 space-y-8">
        {/* Welcome */}
        <div className="rounded-xl border border-line bg-surface p-6 text-center">
          <Users size={32} className="mx-auto text-brand mb-3" />
          <h1 className="text-2xl font-bold text-ink">Welcome, Citizen</h1>
          <p className="mt-2 text-sm text-ink-muted max-w-lg mx-auto">
            Report issues, track your complaints, view city alerts, and access government services — all in one place.
          </p>
          <div className="mt-5 flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              href="/citizen/complaints"
              className="inline-flex items-center gap-2 rounded-lg bg-brand px-5 py-2.5 text-sm font-semibold text-brand-ink hover:bg-brand-strong transition-colors"
            >
              <MessageSquarePlus size={15} />
              Submit a Complaint
            </Link>
            <Link
              href="/citizen/alerts"
              className="inline-flex items-center gap-2 rounded-lg border border-line px-5 py-2.5 text-sm font-semibold text-ink hover:border-brand hover:text-brand transition-colors"
            >
              <Bell size={15} />
              View City Alerts
            </Link>
          </div>
        </div>

        {/* Quick stats */}
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <StatCard label="My Complaints" value={(complaints ?? []).length} />
          <StatCard label="Active Alerts" value={(notifications ?? []).length} color="text-red-400" />
          <StatCard label="Resolved Issues" value={(complaints ?? []).filter(c => c.status === "RESOLVED").length} color="text-emerald-400" />
          <StatCard label="Open Requests" value={(complaints ?? []).filter(c => c.status === "SUBMITTED").length} color="text-amber-400" />
        </div>

        {/* Active Alerts */}
        {(notifications ?? []).length > 0 && (
          <div className="rounded-xl border border-line bg-surface p-5">
            <div className="mb-4 flex items-center gap-2"><Bell size={15} className="text-brand" /><h2 className="text-sm font-semibold text-ink">City Alerts</h2></div>
            <div className="space-y-2">
              {(notifications ?? []).slice(0, 5).map((n) => (
                <div key={n.id} className="flex items-start gap-3 rounded-lg bg-surface-muted/60 px-4 py-3">
                  <span className={`mt-0.5 shrink-0 rounded-full border px-2 py-0.5 text-[9px] font-bold ${severityColor(n.severity)}`}>{n.severity}</span>
                  <div>
                    <p className="text-xs font-semibold text-ink">{n.title}</p>
                    <p className="mt-0.5 text-[11px] text-ink-muted">{n.message}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Complaints */}
        <div className="rounded-xl border border-line bg-surface p-5">
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-2"><MessageSquarePlus size={15} className="text-brand" /><h2 className="text-sm font-semibold text-ink">Recent Complaints</h2></div>
            <Link href="/citizen/complaints" className="text-xs text-brand hover:underline">Submit New +</Link>
          </div>
          <div className="space-y-2">
            {(complaints ?? []).slice(0, 6).map((c) => (
              <div key={c.id} className="flex flex-wrap items-center gap-3 rounded-lg bg-surface-muted/60 px-4 py-3">
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold text-ink truncate">{c.title}</p>
                  <p className="text-[10px] text-ink-faint">{c.complaint_number} · {c.category}</p>
                </div>
                <span className={`rounded-full border px-2 py-0.5 text-[10px] font-medium ${statusColor(c.status)}`}>{c.status}</span>
              </div>
            ))}
            {(complaints?.length ?? 0) === 0 && (
              <div className="flex h-16 items-center justify-center text-sm text-ink-faint">
                No complaints submitted yet
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, color = "text-ink" }: { label: string; value: number; color?: string }) {
  return (
    <div className="rounded-xl border border-line bg-surface p-4 text-center">
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
      <p className="mt-1 text-xs text-ink-muted">{label}</p>
    </div>
  );
}
