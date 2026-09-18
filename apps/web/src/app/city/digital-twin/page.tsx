import { getRoads, getHospitals, getVehicles, getIncidents } from "@/lib/city-api";
import { CityMap } from "@/components/CityMap";

export const metadata = {
  title: "Digital Twin | CityOS",
  description: "Live map of the city's roads, hospitals, vehicles, and incidents.",
};

export default async function DigitalTwinPage() {
  const [roadsRes, hospitalsRes, vehiclesRes, incidentsRes] = await Promise.all([
    getRoads(),
    getHospitals(),
    getVehicles(),
    getIncidents(),
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
            Roads, hospitals, vehicles, and incidents plotted from their real coordinates and
            updated live as the traffic/vehicles providers publish (see Command Center).
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-lg border border-line bg-surface px-3 py-2 text-xs text-ink-muted">
          <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          MapLibre GL
        </div>
      </div>

      <CityMap roads={roads} hospitals={hospitals} vehicles={vehicles} incidents={incidents} />

      <p className="text-xs text-ink-faint">
        Water zones and power substations aren&apos;t shown yet -- their records don&apos;t carry
        real coordinates in city-core&apos;s database, so plotting them here would mean inventing
        a position rather than showing a real one.
      </p>
    </div>
  );
}
