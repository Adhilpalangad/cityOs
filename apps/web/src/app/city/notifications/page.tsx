import { getNotifications } from "@/lib/city-api";
import { severityColor } from "@/lib/colors";
import { BellRing } from "lucide-react";

export const metadata = { title: "Notifications | CityOS", description: "Platform notification center for all departments." };

export default async function NotificationsPage() {
  const notifs = (await getNotifications()) ?? [];
  return (
    <div className="min-h-screen p-6 space-y-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-widest text-brand">Notification Engine</p>
        <h1 className="mt-1 text-2xl font-bold text-ink">Notifications</h1>
        <p className="mt-1 text-sm text-ink-muted">Platform-wide alerts, department notifications, and system events</p>
      </div>
      <div className="rounded-xl border border-line bg-surface p-5">
        <div className="mb-4 flex items-center gap-2"><BellRing size={15} className="text-brand" /><h2 className="text-sm font-semibold text-ink">All Notifications</h2></div>
        <div className="space-y-2">
          {notifs.map((n) => (
            <div key={n.id} className={`flex gap-3 rounded-lg px-4 py-3 ${n.is_read ? "bg-surface-muted/30" : "bg-surface-muted/60 border border-line"}`}>
              <span className={`shrink-0 mt-0.5 rounded-full border px-2 py-0.5 text-[9px] font-bold h-fit ${severityColor(n.severity)}`}>{n.severity}</span>
              <div className="flex-1">
                <p className="text-xs font-semibold text-ink">{n.title}</p>
                <p className="mt-0.5 text-[11px] text-ink-muted">{n.message}</p>
                <div className="mt-1 flex gap-3 text-[10px] text-ink-faint">
                  <span>{n.channel}</span>
                  {n.target_department && <span>→ {n.target_department}</span>}
                </div>
              </div>
              {!n.is_read && <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-brand animate-pulse" />}
            </div>
          ))}
          {notifs.length === 0 && <p className="text-center py-8 text-sm text-ink-faint">No notifications</p>}
        </div>
      </div>
    </div>
  );
}
