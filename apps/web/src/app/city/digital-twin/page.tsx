import {
  getRoads,
  getHospitals,
  getVehicles,
  getIncidents,
  getWaterZones,
  getPowerSubstations,
} from "@/lib/city-api";
import { DigitalTwinMap } from "@/components/DigitalTwinMap";

export const metadata = {
  title: "Digital Twin | CityOS",
  description: "3D/2D digital representation of the city with live asset telemetry visualization.",
};

export default async function DigitalTwinPage() {
  const [roadsRes, hospitalsRes, vehiclesRes, incidentsRes, waterZones, substations] = await Promise.all([
    getRoads(),
    getHospitals(),
    getVehicles(),
    getIncidents(),
    getWaterZones(),
    getPowerSubstations(),
  ]);

  const roads = roadsRes?.items ?? [];
  const hospitals = hospitalsRes?.items ?? [];
  const vehicles = vehiclesRes?.items ?? [];
  const incidents = incidentsRes?.items ?? [];

  return (
    <div className="min-h-screen p-6 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-brand">Real-Time Spatial Model</p>
          <h1 className="mt-1 text-2xl font-bold text-ink">City Digital Twin</h1>
          <p className="mt-1 text-sm text-ink-muted">
            Interactive 2D & 3D digital twin rendering roads, live vehicles, hospitals, emergency incidents, and energy/water grids.
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-lg border border-line bg-surface px-3 py-2 text-xs text-ink-muted">
          <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          WebGL Engine · Active Telemetry Stream
        </div>
      </div>

      {/* Interactive Map Visualizer */}
      <DigitalTwinMap
        roads={roads}
        hospitals={hospitals}
        vehicles={vehicles}
        incidents={incidents}
        waterZones={waterZones}
        substations={substations}
      />
    </div>
  );
}
