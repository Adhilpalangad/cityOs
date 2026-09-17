"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, Cpu, TrafficCone, Bus, Flame, HeartPulse,
  Droplets, Zap, TreePine, Wrench, AlertTriangle, BarChart3,
  FlaskConical, Brain, Globe, Users, ShieldCheck, Search, BellRing,
  ChevronRight
} from "lucide-react";

const nav = [
  { group: "Operations", items: [
    { href: "/city/command-center", icon: LayoutDashboard, label: "Command Center" },
    { href: "/city/digital-twin", icon: Cpu, label: "Digital Twin" },
    { href: "/city/traffic", icon: TrafficCone, label: "Traffic" },
    { href: "/city/transport", icon: Bus, label: "Transport" },
    { href: "/city/emergency", icon: Flame, label: "Emergency" },
    { href: "/city/healthcare", icon: HeartPulse, label: "Healthcare" },
    { href: "/city/water", icon: Droplets, label: "Water" },
    { href: "/city/energy", icon: Zap, label: "Energy" },
    { href: "/city/environment", icon: TreePine, label: "Environment" },
    { href: "/city/infrastructure", icon: Wrench, label: "Infrastructure" },
    { href: "/city/incidents", icon: AlertTriangle, label: "Incidents" },
  ]},
  { group: "Intelligence", items: [
    { href: "/city/analytics", icon: BarChart3, label: "Analytics" },
    { href: "/city/simulation", icon: FlaskConical, label: "Simulation Lab" },
    { href: "/city/ai", icon: Brain, label: "AI Supervisor" },
    { href: "/city/search", icon: Search, label: "Universal Search" },
  ]},
  { group: "Admin", items: [
    { href: "/city/workflows", icon: Globe, label: "Workflows" },
    { href: "/city/audit", icon: ShieldCheck, label: "Audit" },
    { href: "/city/notifications", icon: BellRing, label: "Notifications" },
    { href: "/citizen/portal", icon: Users, label: "Citizen Portal" },
  ]},
];

export function CityNav() {
  const pathname = usePathname();
  return (
    <aside className="flex w-60 flex-shrink-0 flex-col gap-1 border-r border-white/5 bg-[#080e1a] py-4 pr-2 overflow-y-auto">
      {/* Logo */}
      <div className="mb-3 px-4 flex items-center gap-2">
        <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand text-brand-ink font-black text-xs">C</span>
        <span className="text-sm font-bold text-ink tracking-tight">CityOS</span>
      </div>
      {nav.map(({ group, items }) => (
        <div key={group} className="mt-3">
          <p className="mb-1 px-4 text-[10px] font-semibold uppercase tracking-widest text-ink-faint">{group}</p>
          {items.map(({ href, icon: Icon, label }) => {
            const active = pathname === href || pathname.startsWith(href + "/");
            return (
              <Link
                key={href}
                href={href}
                className={`flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-all mx-1 ${
                  active
                    ? "bg-brand/15 text-brand"
                    : "text-ink-muted hover:bg-white/5 hover:text-ink"
                }`}
              >
                <Icon size={15} className={active ? "text-brand" : "text-ink-faint"} />
                {label}
                {active && <ChevronRight size={12} className="ml-auto opacity-60" />}
              </Link>
            );
          })}
        </div>
      ))}
    </aside>
  );
}
