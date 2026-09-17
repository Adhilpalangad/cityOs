import { ComplaintForm } from "@/components/ComplaintForm";
import { getComplaints } from "@/lib/city-api";
import { statusColor } from "@/lib/colors";
import Link from "next/link";

export const metadata = { title: "Submit Complaint | CityOS Citizen Portal", description: "Report city issues and track your complaints." };

export default async function ComplaintsPage() {
  const complaints = (await getComplaints()) ?? [];

  return (
    <div className="min-h-screen bg-[#060b14]">
      <div className="border-b border-line bg-surface/80 px-6 py-4 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between">
          <Link href="/citizen/portal" className="flex items-center gap-2 hover:opacity-80">
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand text-brand-ink font-black text-xs">C</span>
            <span className="text-sm font-bold text-ink">CityOS</span>
          </Link>
          <p className="text-xs text-ink-muted">Citizen Portal</p>
        </div>
      </div>

      <div className="mx-auto max-w-5xl px-6 py-8 space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-ink">Submit a Complaint</h1>
          <p className="mt-1 text-sm text-ink-muted">Report city issues — pothole, water leak, noise, or any civic problem</p>
        </div>

        <div className="grid gap-8 lg:grid-cols-2">
          {/* Form */}
          <div className="rounded-xl border border-line bg-surface p-6">
            <ComplaintForm />
          </div>

          {/* Existing Complaints */}
          <div className="rounded-xl border border-line bg-surface p-6">
            <h2 className="mb-4 text-sm font-semibold text-ink">Recent Complaints</h2>
            <div className="space-y-2">
              {complaints.slice(0, 8).map((c) => (
                <div key={c.id} className="rounded-lg bg-surface-muted/60 p-3">
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-xs font-medium text-ink">{c.title}</p>
                    <span className={`shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-medium ${statusColor(c.status)}`}>{c.status}</span>
                  </div>
                  <p className="mt-0.5 text-[10px] text-ink-faint">{c.complaint_number} · {c.category}</p>
                </div>
              ))}
              {complaints.length === 0 && (
                <p className="text-center py-6 text-sm text-ink-faint">No complaints yet</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
