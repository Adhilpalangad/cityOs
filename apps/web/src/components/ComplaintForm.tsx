"use client";
import { useState, useTransition } from "react";
import { submitComplaint } from "@/lib/city-api";
import type { CitizenComplaint } from "@/lib/city-api";
import { MessageSquarePlus, CheckCircle, Loader2 } from "lucide-react";

const CATEGORIES = ["Infrastructure", "Traffic", "Utilities", "Public Safety", "Sanitation", "Noise", "Environment", "Other"];

export function ComplaintForm() {
  const [pending, startTransition] = useTransition();
  const [submitted, setSubmitted] = useState<CitizenComplaint | null>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("Infrastructure");
  const [email, setEmail] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title || !description) return;
    startTransition(async () => {
      const result = await submitComplaint({
        title,
        description,
        category,
        reporter_email: email || undefined,
      });
      if (result) setSubmitted(result);
    });
  }

  if (submitted) {
    return (
      <div className="flex flex-col items-center gap-4 py-8">
        <CheckCircle size={48} className="text-emerald-400" />
        <div className="text-center">
          <p className="font-semibold text-ink">Complaint Submitted</p>
          <p className="text-sm text-ink-muted mt-1">
            Reference: <span className="font-mono text-brand">{submitted.complaint_number}</span>
          </p>
          <p className="text-xs text-ink-faint mt-1">Your complaint has been assigned to the {submitted.department_code} department.</p>
        </div>
        <button
          onClick={() => { setSubmitted(null); setTitle(""); setDescription(""); }}
          className="rounded-lg border border-line px-4 py-2 text-sm text-ink hover:border-brand hover:text-brand transition-colors"
        >
          Submit Another
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="complaint-title" className="block text-xs font-medium text-ink-muted mb-1">Issue Title *</label>
        <input
          id="complaint-title"
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="e.g., Large pothole on Main Street"
          required
          className="w-full rounded-lg border border-line bg-surface-muted px-3 py-2.5 text-sm text-ink placeholder-ink-faint focus:border-brand focus:outline-none"
        />
      </div>
      <div>
        <label htmlFor="complaint-category" className="block text-xs font-medium text-ink-muted mb-1">Category</label>
        <select
          id="complaint-category"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="w-full rounded-lg border border-line bg-surface-muted px-3 py-2.5 text-sm text-ink focus:border-brand focus:outline-none"
        >
          {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
        </select>
      </div>
      <div>
        <label htmlFor="complaint-desc" className="block text-xs font-medium text-ink-muted mb-1">Description *</label>
        <textarea
          id="complaint-desc"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={4}
          placeholder="Describe the issue in detail…"
          required
          className="w-full rounded-lg border border-line bg-surface-muted px-3 py-2.5 text-sm text-ink placeholder-ink-faint focus:border-brand focus:outline-none resize-none"
        />
      </div>
      <div>
        <label htmlFor="complaint-email" className="block text-xs font-medium text-ink-muted mb-1">Email (optional)</label>
        <input
          id="complaint-email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
          className="w-full rounded-lg border border-line bg-surface-muted px-3 py-2.5 text-sm text-ink placeholder-ink-faint focus:border-brand focus:outline-none"
        />
      </div>
      <button
        id="complaint-submit-btn"
        type="submit"
        disabled={pending || !title || !description}
        className="flex w-full items-center justify-center gap-2 rounded-lg bg-brand px-4 py-2.5 text-sm font-semibold text-brand-ink shadow-sm hover:bg-brand-strong disabled:opacity-50 transition-all"
      >
        {pending ? <><Loader2 size={14} className="animate-spin" /> Submitting…</> : <><MessageSquarePlus size={14} /> Submit Complaint</>}
      </button>
    </form>
  );
}
