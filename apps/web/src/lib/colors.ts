// Shared severity/status badge utility
export type Severity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" | string;
export type TrafficLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" | string;

export function severityColor(s: Severity): string {
  switch (s) {
    case "CRITICAL":
      return "bg-red-500/15 text-red-400 border-red-500/30";
    case "HIGH":
      return "bg-orange-500/15 text-orange-400 border-orange-500/30";
    case "MEDIUM":
      return "bg-yellow-500/15 text-yellow-400 border-yellow-500/30";
    case "LOW":
      return "bg-emerald-500/15 text-emerald-400 border-emerald-500/30";
    default:
      return "bg-sky-500/15 text-sky-400 border-sky-500/30";
  }
}

export function statusColor(s: string): string {
  switch (s) {
    case "OPERATIONAL":
    case "ACTIVE":
    case "OPEN":
    case "RESOLVED":
    case "COMPLETED":
      return "bg-emerald-500/15 text-emerald-400 border-emerald-500/30";
    case "LIMITED":
    case "MAINTENANCE":
    case "WARNING":
      return "bg-yellow-500/15 text-yellow-400 border-yellow-500/30";
    case "CLOSED":
    case "DETECTED":
    case "CRITICAL":
      return "bg-red-500/15 text-red-400 border-red-500/30";
    case "IN_PROGRESS":
    case "RESPONDING":
      return "bg-sky-500/15 text-sky-400 border-sky-500/30";
    case "SUBMITTED":
    case "PENDING":
    case "VERIFIED":
    case "ASSIGNED":
      return "bg-violet-500/15 text-violet-400 border-violet-500/30";
    default:
      return "bg-slate-500/15 text-slate-400 border-slate-500/30";
  }
}

export function trafficDotColor(level: TrafficLevel): string {
  switch (level) {
    case "CRITICAL": return "bg-red-500";
    case "HIGH": return "bg-orange-400";
    case "MEDIUM": return "bg-yellow-400";
    default: return "bg-emerald-400";
  }
}
