"use client";

import { useEffect, useState } from "react";
import {
  Layers, Play, Pause, AlertTriangle, HeartPulse, Car,
  Zap, Droplet, Eye, EyeOff, Activity
} from "lucide-react";
import type { Road, Hospital, Vehicle, Incident, WaterZone, PowerSubstation } from "@/lib/city-api";

interface DigitalTwinMapProps {
  roads: Road[];
  hospitals: Hospital[];
  vehicles: Vehicle[];
  incidents: Incident[];
  waterZones: WaterZone[];
  substations: PowerSubstation[];
}

export function DigitalTwinMap({
  roads,
  hospitals,
  vehicles,
  incidents,
  waterZones,
  substations,
}: DigitalTwinMapProps) {
  // Layer Toggles
  const [layers, setLayers] = useState({
    roads: true,
    vehicles: true,
    hospitals: true,
    incidents: true,
    water: true,
    power: true,
    radar: true,
  });

  // Mode: '2d' | '3d'
  const [viewMode, setViewMode] = useState<"2d" | "3d">("2d");
  const [isPlaying, setIsPlaying] = useState(true);
  const [speed, setSpeed] = useState<number>(1);
  const [selectedEntity, setSelectedEntity] = useState<{
    type: "road" | "hospital" | "vehicle" | "incident" | "water" | "power";
    data: Record<string, unknown>;
  } | null>(null);

  // Animated vehicle offsets
  const [vehicleTicks, setVehicleTicks] = useState(0);

  useEffect(() => {
    if (!isPlaying) return;
    const interval = setInterval(() => {
      setVehicleTicks((t) => t + 1);
    }, 1000 / speed);
    return () => clearInterval(interval);
  }, [isPlaying, speed]);

  const toggleLayer = (key: keyof typeof layers) => {
    setLayers((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="relative flex flex-col lg:flex-row h-[720px] w-full rounded-2xl border border-line bg-[#0B0F17] overflow-hidden text-ink shadow-2xl">
      {/* Sidebar Control Panel */}
      <div className="w-full lg:w-72 shrink-0 border-b lg:border-b-0 lg:border-r border-line/60 bg-[#0E1420]/90 backdrop-blur-md p-4 flex flex-col justify-between space-y-4 z-20">
        <div>
          <div className="flex items-center justify-between pb-3 border-b border-line/40">
            <div className="flex items-center gap-2">
              <div className="h-3 w-3 rounded-full bg-brand animate-ping" />
              <span className="text-xs font-bold uppercase tracking-wider text-brand">Live Twin</span>
            </div>
            <span className="rounded-md bg-surface-muted px-2 py-0.5 text-[10px] font-mono text-ink-muted">
              {viewMode.toUpperCase()} Engine
            </span>
          </div>

          {/* View Mode & Simulation Speed Controls */}
          <div className="mt-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-ink-muted">Perspective Mode</span>
              <div className="flex rounded-lg border border-line/60 p-0.5 bg-surface/50">
                <button
                  onClick={() => setViewMode("2d")}
                  className={`px-2.5 py-1 text-[11px] font-semibold rounded-md transition-all ${
                    viewMode === "2d" ? "bg-brand text-white shadow" : "text-ink-muted hover:text-ink"
                  }`}
                >
                  2D Grid
                </button>
                <button
                  onClick={() => setViewMode("3d")}
                  className={`px-2.5 py-1 text-[11px] font-semibold rounded-md transition-all ${
                    viewMode === "3d" ? "bg-brand text-white shadow" : "text-ink-muted hover:text-ink"
                  }`}
                >
                  3D Isometric
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-ink-muted">Telemetry Stream</span>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setIsPlaying(!isPlaying)}
                  className="p-1.5 rounded-md border border-line/60 bg-surface-muted/60 text-ink hover:bg-surface-muted text-xs"
                >
                  {isPlaying ? <Pause size={12} /> : <Play size={12} />}
                </button>
                {[1, 2, 5].map((s) => (
                  <button
                    key={s}
                    onClick={() => setSpeed(s)}
                    className={`px-2 py-1 text-[10px] font-mono font-bold rounded-md border transition-all ${
                      speed === s ? "border-brand bg-brand/10 text-brand" : "border-line/40 text-ink-muted"
                    }`}
                  >
                    {s}x
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Layer Toggles */}
          <div className="mt-5 space-y-2">
            <p className="text-[11px] font-bold uppercase tracking-wider text-ink-muted mb-2 flex items-center gap-1.5">
              <Layers size={13} /> Active Layers
            </p>

            <LayerToggleItem
              label="Road Traffic Network"
              icon={<Car size={13} className="text-amber-400" />}
              active={layers.roads}
              count={roads.length}
              onClick={() => toggleLayer("roads")}
            />
            <LayerToggleItem
              label="Live Vehicles & Fleet"
              icon={<Activity size={13} className="text-cyan-400" />}
              active={layers.vehicles}
              count={vehicles.length}
              onClick={() => toggleLayer("vehicles")}
            />
            <LayerToggleItem
              label="Hospitals & ER Capacity"
              icon={<HeartPulse size={13} className="text-pink-400" />}
              active={layers.hospitals}
              count={hospitals.length}
              onClick={() => toggleLayer("hospitals")}
            />
            <LayerToggleItem
              label="Emergency Incidents"
              icon={<AlertTriangle size={13} className="text-red-400" />}
              active={layers.incidents}
              count={incidents.length}
              onClick={() => toggleLayer("incidents")}
            />
            <LayerToggleItem
              label="Power Grid Substations"
              icon={<Zap size={13} className="text-yellow-400" />}
              active={layers.power}
              count={substations.length}
              onClick={() => toggleLayer("power")}
            />
            <LayerToggleItem
              label="Water Supply Zones"
              icon={<Droplet size={13} className="text-blue-400" />}
              active={layers.water}
              count={waterZones.length}
              onClick={() => toggleLayer("water")}
            />
          </div>
        </div>

        {/* Selected Entity Inspector */}
        {selectedEntity ? (
          <div className="rounded-xl border border-brand/40 bg-brand/5 p-3 space-y-2 transition-all">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-brand">
                Inspector · {selectedEntity.type}
              </span>
              <button
                onClick={() => setSelectedEntity(null)}
                className="text-[10px] text-ink-muted hover:text-ink"
              >
                ✕
              </button>
            </div>
            <p className="text-xs font-semibold text-ink truncate">
              {selectedEntity.data.name || selectedEntity.data.incident_number || selectedEntity.data.vehicle_id}
            </p>
            <div className="text-[10px] space-y-1 text-ink-muted">
              {selectedEntity.type === "incident" && (
                <>
                  <p>Severity: <strong className="text-red-400">{selectedEntity.data.severity}</strong></p>
                  <p>Status: <strong className="text-amber-400">{selectedEntity.data.status}</strong></p>
                  <p className="line-clamp-2">{selectedEntity.data.description}</p>
                </>
              )}
              {selectedEntity.type === "hospital" && (
                <>
                  <p>Beds Occupied: <strong>{selectedEntity.data.beds_occupied} / {selectedEntity.data.beds_total}</strong></p>
                  <p>ICU Occupied: <strong className="text-pink-400">{selectedEntity.data.icu_occupied} / {selectedEntity.data.icu_total}</strong></p>
                </>
              )}
              {selectedEntity.type === "road" && (
                <>
                  <p>Traffic Level: <strong className="text-amber-400">{selectedEntity.data.traffic_level}</strong></p>
                  <p>Speed: <strong>{selectedEntity.data.average_speed_kmh} km/h</strong></p>
                </>
              )}
              {selectedEntity.type === "vehicle" && (
                <>
                  <p>Type: <strong>{selectedEntity.data.vehicle_type}</strong></p>
                  <p>Speed: <strong>{selectedEntity.data.speed_kmh} km/h</strong></p>
                </>
              )}
            </div>
          </div>
        ) : (
          <div className="rounded-xl border border-line/40 bg-surface/30 p-3 text-center text-[11px] text-ink-faint">
            Click any road, hospital, vehicle, or incident marker to inspect live telemetry.
          </div>
        )}
      </div>

      {/* Main Canvas Viewport */}
      <div className="relative flex-1 h-full bg-[#080C14] overflow-hidden flex items-center justify-center select-none">
        {/* Grid Background */}
        <div
          className="absolute inset-0 opacity-20 pointer-events-none"
          style={{
            backgroundImage: `radial-gradient(#3B82F6 1px, transparent 1px), radial-gradient(#1E293B 1px, transparent 1px)`,
            backgroundSize: "32px 32px",
            backgroundPosition: "0 0, 16px 16px",
          }}
        />

        {/* 2D / 3D Render Canvas Container */}
        <div
          className={`relative w-[900px] h-[600px] transition-all duration-700 ${
            viewMode === "3d" ? "scale-90 rotate-x-45 -rotate-z-12 perspective-1000 shadow-2xl" : ""
          }`}
          style={{
            transformStyle: viewMode === "3d" ? "preserve-3d" : "flat",
          }}
        >
          {/* Base Map Grid & Zones */}
          <svg className="absolute inset-0 w-full h-full" viewBox="0 0 900 600">
            <defs>
              <linearGradient id="roadGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#3B82F6" stopOpacity="0.8" />
                <stop offset="100%" stopColor="#8B5CF6" stopOpacity="0.8" />
              </linearGradient>
              <linearGradient id="roadHigh" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#EF4444" stopOpacity="0.9" />
                <stop offset="100%" stopColor="#F59E0B" stopOpacity="0.9" />
              </linearGradient>
              <filter id="glow">
                <feGaussianBlur stdDeviation="3" result="coloredBlur" />
                <feMerge>
                  <feMergeNode in="coloredBlur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            {/* City Districts Polygons */}
            <polygon points="50,50 320,40 380,240 80,260" fill="#1E293B" fillOpacity="0.25" stroke="#334155" strokeDasharray="4,4" />
            <polygon points="340,40 820,30 850,280 400,260" fill="#1E293B" fillOpacity="0.2" stroke="#334155" strokeDasharray="4,4" />
            <polygon points="80,280 400,280 420,550 50,540" fill="#1E293B" fillOpacity="0.3" stroke="#334155" strokeDasharray="4,4" />
            <polygon points="420,280 860,290 840,560 440,550" fill="#1E293B" fillOpacity="0.2" stroke="#334155" strokeDasharray="4,4" />

            {/* Labels */}
            <text x="120" y="90" fill="#475569" fontSize="12" fontWeight="700" letterSpacing="2">NORTH METRO</text>
            <text x="520" y="90" fill="#475569" fontSize="12" fontWeight="700" letterSpacing="2">TECH PARK & HARBOR</text>
            <text x="120" y="340" fill="#475569" fontSize="12" fontWeight="700" letterSpacing="2">COMMERCIAL GRID</text>
            <text x="520" y="340" fill="#475569" fontSize="12" fontWeight="700" letterSpacing="2">SOUTH COASTAL ZONE</text>

            {/* Water Supply Zones Overlay */}
            {layers.water && (
              <>
                <circle cx="240" cy="410" r="120" fill="#3B82F6" fillOpacity="0.08" stroke="#3B82F6" strokeWidth="1.5" strokeDasharray="6,4" />
                <text x="200" y="490" fill="#60A5FA" fontSize="10" fontWeight="600">WZ-CENTRAL (3.5M L)</text>
              </>
            )}

            {/* Power Grid Lines */}
            {layers.power && (
              <g stroke="#EAB308" strokeWidth="1.5" strokeDasharray="5,5" opacity="0.6">
                <line x1="200" y1="160" x2="650" y2="180" />
                <line x1="650" y1="180" x2="700" y2="440" />
              </g>
            )}

            {/* Roads Layer */}
            {layers.roads && (
              <g filter="url(#glow)">
                {/* Road 1: Grand Coastal */}
                <path
                  d="M 100 150 Q 300 120 500 180 T 800 200"
                  fill="none"
                  stroke={roads[0]?.traffic_level === "HIGH" ? "url(#roadHigh)" : "url(#roadGrad)"}
                  strokeWidth="8"
                  strokeLinecap="round"
                  className="cursor-pointer hover:stroke-brand transition-all"
                  onClick={() => setSelectedEntity({ type: "road", data: roads[0] || { name: "Grand Coastal Arterial", traffic_level: "HIGH", average_speed_kmh: 42 } })}
                />
                {/* Road 2: Central Boulevard */}
                <path
                  d="M 220 80 L 240 500"
                  fill="none"
                  stroke="#3B82F6"
                  strokeWidth="6"
                  strokeLinecap="round"
                  className="cursor-pointer hover:stroke-brand transition-all"
                  onClick={() => setSelectedEntity({ type: "road", data: roads[1] || { name: "Metro Central Boulevard", traffic_level: "LOW", average_speed_kmh: 58 } })}
                />
                {/* Road 3: Tech Corridor Bypass */}
                <path
                  d="M 120 420 L 780 440"
                  fill="none"
                  stroke="#EF4444"
                  strokeWidth="7"
                  strokeLinecap="round"
                  strokeDasharray="12,4"
                  className="cursor-pointer hover:stroke-red-400 transition-all"
                  onClick={() => setSelectedEntity({ type: "road", data: roads[2] || { name: "Tech Corridor Bypass", traffic_level: "CRITICAL", average_speed_kmh: 28 } })}
                />
              </g>
            )}

            {/* Live Vehicle Animation along Road 1 */}
            {layers.vehicles && (
              <g>
                {/* Vehicle 1 */}
                <circle
                  cx={100 + ((vehicleTicks * 15) % 680)}
                  cy={150 + Math.sin(vehicleTicks * 0.1) * 20}
                  r="6"
                  fill="#06B6D4"
                  stroke="#FFFFFF"
                  strokeWidth="2"
                  filter="url(#glow)"
                  className="cursor-pointer transition-all"
                  onClick={() => setSelectedEntity({ type: "vehicle", data: vehicles[0] || { vehicle_id: "AMB-101", vehicle_type: "ambulance", speed_kmh: 65 } })}
                />
                {/* Vehicle 2 */}
                <circle
                  cx={240}
                  cy={80 + ((vehicleTicks * 12) % 400)}
                  r="6"
                  fill="#F59E0B"
                  stroke="#FFFFFF"
                  strokeWidth="2"
                  filter="url(#glow)"
                  className="cursor-pointer transition-all"
                  onClick={() => setSelectedEntity({ type: "vehicle", data: vehicles[1] || { vehicle_id: "BUS-402", vehicle_type: "public_transport", speed_kmh: 35 } })}
                />
              </g>
            )}
          </svg>

          {/* Hospitals Layer Markers (DOM overlay with custom badges) */}
          {layers.hospitals && (
            <>
              {/* Hospital 1 */}
              <div
                className="absolute top-[130px] left-[480px] -translate-x-1/2 -translate-y-1/2 cursor-pointer group"
                onClick={() => setSelectedEntity({ type: "hospital", data: hospitals[0] || { name: "Central Metropolitan Hospital", beds_occupied: 380, beds_total: 450, icu_occupied: 52, icu_total: 60 } })}
              >
                <div className="flex items-center gap-1.5 rounded-full border border-pink-500/60 bg-[#0E1420]/90 px-2.5 py-1 shadow-lg group-hover:scale-110 transition-transform">
                  <HeartPulse size={12} className="text-pink-400 animate-pulse" />
                  <span className="text-[10px] font-bold text-pink-300">Central Metro ER</span>
                </div>
              </div>

              {/* Hospital 2 */}
              <div
                className="absolute top-[390px] left-[680px] -translate-x-1/2 -translate-y-1/2 cursor-pointer group"
                onClick={() => setSelectedEntity({ type: "hospital", data: hospitals[1] || { name: "St. Jude Emergency Center", beds_occupied: 142, beds_total: 150, icu_occupied: 19, icu_total: 20 } })}
              >
                <div className="flex items-center gap-1.5 rounded-full border border-red-500/80 bg-[#0E1420]/90 px-2.5 py-1 shadow-lg group-hover:scale-110 transition-transform">
                  <HeartPulse size={12} className="text-red-400 animate-bounce" />
                  <span className="text-[10px] font-bold text-red-300">St. Jude ER (95%)</span>
                </div>
              </div>
            </>
          )}

          {/* Emergency Incidents Radar Pulsing Markers */}
          {layers.incidents && (
            <>
              {/* Incident 1: Critical Traffic Crash */}
              <div
                className="absolute top-[415px] left-[420px] -translate-x-1/2 -translate-y-1/2 cursor-pointer group"
                onClick={() => setSelectedEntity({ type: "incident", data: incidents[0] || { incident_number: "INC-2026-0891", severity: "CRITICAL", status: "DISPATCHED", description: "Multi-vehicle collision on Tech Corridor" } })}
              >
                <div className="relative flex items-center justify-center">
                  <span className="absolute h-10 w-10 rounded-full bg-red-500/40 animate-ping" />
                  <div className="relative flex items-center gap-1 rounded-md border border-red-500 bg-red-950/90 px-2 py-0.5 shadow-xl text-red-200 text-[10px] font-bold">
                    <AlertTriangle size={12} className="text-red-400" />
                    <span>INC-0891</span>
                  </div>
                </div>
              </div>

              {/* Incident 2: Power Outage */}
              <div
                className="absolute top-[175px] left-[640px] -translate-x-1/2 -translate-y-1/2 cursor-pointer group"
                onClick={() => setSelectedEntity({ type: "incident", data: incidents[1] || { incident_number: "INC-2026-0892", severity: "HIGH", status: "IN_PROGRESS", description: "Transformer outage in East district" } })}
              >
                <div className="relative flex items-center justify-center">
                  <span className="absolute h-8 w-8 rounded-full bg-amber-500/40 animate-ping" />
                  <div className="relative flex items-center gap-1 rounded-md border border-amber-500 bg-amber-950/90 px-2 py-0.5 shadow-xl text-amber-200 text-[10px] font-bold">
                    <Zap size={12} className="text-amber-400" />
                    <span>Power Trip</span>
                  </div>
                </div>
              </div>
            </>
          )}

          {/* Power Substations */}
          {layers.power && (
            <div
              className="absolute top-[180px] left-[650px] -translate-x-1/2 -translate-y-1/2 cursor-pointer"
              onClick={() => setSelectedEntity({ type: "power", data: substations[0] || { name: "Grand Coastal Substation Alpha", capacity_mw: 250, load_mw: 195 } })}
            >
              <div className="flex items-center gap-1 rounded-md border border-yellow-500/60 bg-[#0E1420] px-1.5 py-0.5 text-[9px] text-yellow-300 font-bold">
                <Zap size={10} /> SUB-01 (195 MW)
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function LayerToggleItem({
  label, icon, active, count, onClick,
}: {
  label: string;
  icon: React.ReactNode;
  active: boolean;
  count: number;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center justify-between p-2 rounded-lg border text-left transition-all ${
        active
          ? "border-line bg-surface/70 text-ink shadow-sm"
          : "border-transparent bg-transparent text-ink-faint hover:text-ink-muted"
      }`}
    >
      <div className="flex items-center gap-2">
        {icon}
        <span className="text-xs font-medium">{label}</span>
      </div>
      <div className="flex items-center gap-1.5">
        <span className="rounded-full bg-surface-muted px-1.5 py-0.2 text-[10px] font-mono text-ink-muted">
          {count}
        </span>
        {active ? <Eye size={12} className="text-brand" /> : <EyeOff size={12} className="text-ink-faint" />}
      </div>
    </button>
  );
}
