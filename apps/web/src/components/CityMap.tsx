"use client";

import { MapLibreMap, NavigationControl } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useRef, useState } from "react";
import type { Feature, FeatureCollection, LineString, Point } from "geojson";
import type { GeoJSONSource, MapLayerMouseEvent, StyleSpecification } from "maplibre-gl";
import type { Hospital, Incident, Road, Vehicle } from "@/lib/city-api";
import { useLiveFeed } from "@/lib/live-socket";

/**
 * Replaces the old decorative SVG "digital twin" (hardcoded pixel positions
 * unrelated to any real data) with a real MapLibre map: roads render from
 * their actual `waypoints`, hospitals/vehicles/incidents from their actual
 * `latitude`/`longitude`, and clicking a feature inspects the real record
 * behind it. Roads and vehicles also merge in live updates from
 * `useLiveFeed()` (Phase 3), so the map moves when the traffic/vehicles
 * providers publish a new tick -- no polling, no page refresh.
 *
 * Water zones and power substations are deliberately not shown here: their
 * DB models (services/city-core/app/db/models.py) carry no lat/lon today,
 * so plotting them would mean inventing a position, which is exactly the
 * "decorative, disconnected from real data" problem this component exists
 * to fix (spec section 86). They get real markers once those tables gain
 * real coordinates.
 */

const OSM_STYLE: StyleSpecification = {
  version: 8,
  sources: {
    osm: {
      type: "raster",
      tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
      tileSize: 256,
      attribution: "&copy; OpenStreetMap contributors",
    },
  },
  layers: [{ id: "osm", type: "raster", source: "osm" }],
};

type Selected =
  | { kind: "road"; data: Road }
  | { kind: "hospital"; data: Hospital }
  | { kind: "vehicle"; data: Vehicle }
  | { kind: "incident"; data: Incident };

interface CityMapProps {
  roads: Road[];
  hospitals: Hospital[];
  vehicles: Vehicle[];
  incidents: Incident[];
}

function roadsToFeatures(roads: Road[]): FeatureCollection<LineString> {
  return {
    type: "FeatureCollection",
    features: roads
      .filter((r) => r.waypoints.length >= 2)
      .map(
        (r): Feature<LineString> => ({
          type: "Feature",
          properties: { code: r.code },
          geometry: {
            type: "LineString",
            // waypoints are stored [lat, lon]; GeoJSON/MapLibre want [lon, lat].
            coordinates: r.waypoints.map(([lat, lon]) => [lon, lat]),
          },
        })
      ),
  };
}

function pointsToFeatures<T extends { latitude: number | null; longitude: number | null }>(
  items: T[],
  idOf: (item: T) => string
): FeatureCollection<Point> {
  return {
    type: "FeatureCollection",
    features: items
      .filter((item): item is T & { latitude: number; longitude: number } =>
        item.latitude != null && item.longitude != null
      )
      .map(
        (item): Feature<Point> => ({
          type: "Feature",
          properties: { _id: idOf(item) },
          geometry: { type: "Point", coordinates: [item.longitude, item.latitude] },
        })
      ),
  };
}

function firstCenter(roads: Road[], hospitals: Hospital[]): [number, number] {
  const road = roads.find((r) => r.waypoints.length > 0);
  if (road) {
    const [lat, lon] = road.waypoints[0];
    return [lon, lat];
  }
  const hospital = hospitals[0];
  if (hospital) return [hospital.longitude, hospital.latitude];
  return [75.7817, 11.2506]; // fallback: Kozhikode city centre (Mananchira)
}

export function CityMap({ roads: initialRoads, hospitals, vehicles: initialVehicles, incidents: initialIncidents }: CityMapProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const [styleLoaded, setStyleLoaded] = useState(false);
  const [selected, setSelected] = useState<Selected | null>(null);
  const [layers, setLayers] = useState({ roads: true, hospitals: true, vehicles: true, incidents: true });

  const { roads: liveRoads, vehicles: liveVehicles, incidents: liveIncidents, connected } = useLiveFeed();

  const roads = mergeByKey(initialRoads, liveRoads, (r) => r.code);
  const vehicles = mergeByKey(initialVehicles, liveVehicles, (v) => v.vehicle_id);
  // Incidents are never upserted -- every provider/API event is a genuinely
  // new row (app/services/live_ingest.py's apply_incident_event always
  // INSERTs). mergeByKey still does the right thing here: a live incident's
  // id never matches one already in initialIncidents, so every live entry
  // just appends rather than replacing anything.
  const incidents = mergeByKey(initialIncidents, liveIncidents, (i) => i.id);

  // Latest data, readable from the one-time init effect below without
  // retriggering it (that effect must only run once -- creating a
  // MapLibreMap is expensive and it manages its own internal state). Kept
  // current in its own effect rather than assigned during render, since
  // refs shouldn't be written while rendering.
  const latest = useRef({ roads, hospitals, vehicles, incidents });
  useEffect(() => {
    latest.current = { roads, hospitals, vehicles, incidents };
  });

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = new MapLibreMap({
      container: containerRef.current,
      style: OSM_STYLE,
      center: firstCenter(latest.current.roads, latest.current.hospitals),
      zoom: 12,
    });
    map.addControl(new NavigationControl(), "top-right");
    mapRef.current = map;

    map.on("load", () => {
      map.addSource("roads", { type: "geojson", data: roadsToFeatures(latest.current.roads) });
      map.addLayer({
        id: "roads-layer",
        type: "line",
        source: "roads",
        layout: { "line-cap": "round", "line-join": "round" },
        paint: {
          "line-width": 5,
          // Inlined (rather than a separately-typed constant) so it's
          // checked contextually against addLayer()'s paint type --
          // maplibre-gl doesn't export a standalone "expression" type in
          // this version, and a `const` array's inferred readonly tuple
          // type doesn't structurally match the mutable one it expects.
          "line-color": [
            "match",
            ["get", "traffic_level"],
            "LOW",
            "#22c55e",
            "MEDIUM",
            "#eab308",
            "HIGH",
            "#f97316",
            "CRITICAL",
            "#ef4444",
            "#3b82f6",
          ],
        },
      });

      map.addSource("hospitals", {
        type: "geojson",
        data: pointsToFeatures(latest.current.hospitals, (h) => h.id),
      });
      map.addLayer({
        id: "hospitals-layer",
        type: "circle",
        source: "hospitals",
        paint: {
          "circle-radius": 7,
          "circle-color": "#ec4899",
          "circle-stroke-width": 2,
          "circle-stroke-color": "#ffffff",
        },
      });

      map.addSource("vehicles", {
        type: "geojson",
        data: pointsToFeatures(latest.current.vehicles, (v) => v.vehicle_id),
      });
      map.addLayer({
        id: "vehicles-layer",
        type: "circle",
        source: "vehicles",
        paint: {
          "circle-radius": 5,
          "circle-color": "#06b6d4",
          "circle-stroke-width": 1.5,
          "circle-stroke-color": "#ffffff",
        },
      });

      map.addSource("incidents", {
        type: "geojson",
        data: pointsToFeatures(latest.current.incidents, (i) => i.id),
      });
      // Pulsing halo, drawn *under* the solid dot below: an expanding,
      // fading ring so a new incident reads as "blinking" on the map,
      // matching the ask ("small node is blinking in map"). Its radius/
      // opacity are animated by the requestAnimationFrame loop further
      // down -- MapLibre has no built-in pulse, so this drives the paint
      // properties by hand every frame.
      map.addLayer({
        id: "incidents-pulse-layer",
        type: "circle",
        source: "incidents",
        paint: {
          "circle-radius": 8,
          "circle-color": "#ef4444",
          "circle-opacity": 0.5,
          "circle-stroke-width": 0,
        },
      });
      map.addLayer({
        id: "incidents-layer",
        type: "circle",
        source: "incidents",
        paint: {
          "circle-radius": 8,
          "circle-color": "#ef4444",
          "circle-stroke-width": 2,
          "circle-stroke-color": "#fecaca",
        },
      });

      for (const layerId of [
        "roads-layer",
        "hospitals-layer",
        "vehicles-layer",
        "incidents-pulse-layer",
        "incidents-layer",
      ]) {
        map.on("mouseenter", layerId, () => {
          map.getCanvas().style.cursor = "pointer";
        });
        map.on("mouseleave", layerId, () => {
          map.getCanvas().style.cursor = "";
        });
      }

      map.on("click", "roads-layer", (e: MapLayerMouseEvent) => {
        const code = e.features?.[0]?.properties?.code as string | undefined;
        const road = latest.current.roads.find((r) => r.code === code);
        if (road) setSelected({ kind: "road", data: road });
      });
      map.on("click", "hospitals-layer", (e: MapLayerMouseEvent) => {
        const id = e.features?.[0]?.properties?._id as string | undefined;
        const hospital = latest.current.hospitals.find((h) => h.id === id);
        if (hospital) setSelected({ kind: "hospital", data: hospital });
      });
      map.on("click", "vehicles-layer", (e: MapLayerMouseEvent) => {
        const id = e.features?.[0]?.properties?._id as string | undefined;
        const vehicle = latest.current.vehicles.find((v) => v.vehicle_id === id);
        if (vehicle) setSelected({ kind: "vehicle", data: vehicle });
      });
      const selectIncident = (e: MapLayerMouseEvent) => {
        const id = e.features?.[0]?.properties?._id as string | undefined;
        const incident = latest.current.incidents.find((i) => i.id === id);
        if (incident) setSelected({ kind: "incident", data: incident });
      };
      // Registered on both the solid dot and its pulsing halo -- the halo's
      // radius grows past the dot's, so without this a click that lands in
      // the pulse ring (rather than dead-center) would miss.
      map.on("click", "incidents-layer", selectIncident);
      map.on("click", "incidents-pulse-layer", selectIncident);

      setStyleLoaded(true);
    });

    // Pulse animation: oscillate the halo layer's radius/opacity so new
    // incidents read as "blinking" on the map rather than a static dot.
    // Runs continuously for every incident marker (not just newly-arrived
    // ones) -- simpler than tracking a "new since when" set per marker, and
    // still satisfies the ask that a node visibly blinks.
    let pulseFrame: number;
    const pulseStart = performance.now();
    function pulse(now: number) {
      const map = mapRef.current;
      if (map?.getLayer("incidents-pulse-layer")) {
        const t = ((now - pulseStart) / 1000) % 1.4; // 1.4s cycle
        const progress = t / 1.4;
        map.setPaintProperty("incidents-pulse-layer", "circle-radius", 8 + progress * 16);
        map.setPaintProperty("incidents-pulse-layer", "circle-opacity", 0.5 * (1 - progress));
      }
      pulseFrame = requestAnimationFrame(pulse);
    }
    pulseFrame = requestAnimationFrame(pulse);

    return () => {
      cancelAnimationFrame(pulseFrame);
      map.remove();
      mapRef.current = null;
    };
    // Intentionally empty -- see the `latest` ref above for why this only
    // runs once.
  }, []);

  // Keep each source's data current as props/live updates change.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !styleLoaded) return;
    (map.getSource("roads") as GeoJSONSource | undefined)?.setData(roadsToFeatures(roads));
  }, [roads, styleLoaded]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !styleLoaded) return;
    (map.getSource("hospitals") as GeoJSONSource | undefined)?.setData(
      pointsToFeatures(hospitals, (h) => h.id)
    );
  }, [hospitals, styleLoaded]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !styleLoaded) return;
    (map.getSource("vehicles") as GeoJSONSource | undefined)?.setData(
      pointsToFeatures(vehicles, (v) => v.vehicle_id)
    );
  }, [vehicles, styleLoaded]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !styleLoaded) return;
    (map.getSource("incidents") as GeoJSONSource | undefined)?.setData(
      pointsToFeatures(incidents, (i) => i.id)
    );
  }, [incidents, styleLoaded]);

  // Layer toggles.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !styleLoaded) return;
    const visibility = (on: boolean) => (on ? "visible" : "none");
    map.setLayoutProperty("roads-layer", "visibility", visibility(layers.roads));
    map.setLayoutProperty("hospitals-layer", "visibility", visibility(layers.hospitals));
    map.setLayoutProperty("vehicles-layer", "visibility", visibility(layers.vehicles));
    map.setLayoutProperty("incidents-layer", "visibility", visibility(layers.incidents));
    map.setLayoutProperty("incidents-pulse-layer", "visibility", visibility(layers.incidents));
  }, [layers, styleLoaded]);

  return (
    <div className="relative flex flex-col lg:flex-row h-[720px] w-full rounded-2xl border border-line bg-[#0B0F17] overflow-hidden text-ink shadow-2xl">
      <div className="w-full lg:w-72 shrink-0 border-b lg:border-b-0 lg:border-r border-line/60 bg-[#0E1420]/90 backdrop-blur-md p-4 flex flex-col justify-between space-y-4 z-10 overflow-y-auto">
        <div>
          <div className="flex items-center justify-between pb-3 border-b border-line/40">
            <div className="flex items-center gap-2">
              <span className={`h-2.5 w-2.5 rounded-full ${connected ? "bg-emerald-400 animate-pulse" : "bg-ink-faint"}`} />
              <span className="text-xs font-bold uppercase tracking-wider text-brand">City Map</span>
            </div>
            <span className="rounded-md bg-surface-muted px-2 py-0.5 text-[10px] font-mono text-ink-muted">
              {connected ? "Live" : "DB snapshot"}
            </span>
          </div>

          <div className="mt-4 space-y-2">
            <p className="text-[11px] font-bold uppercase tracking-wider text-ink-muted mb-2">Layers</p>
            <LayerToggle label="Roads" color="#3b82f6" count={roads.length} active={layers.roads} onClick={() => setLayers((p) => ({ ...p, roads: !p.roads }))} />
            <LayerToggle label="Hospitals" color="#ec4899" count={hospitals.length} active={layers.hospitals} onClick={() => setLayers((p) => ({ ...p, hospitals: !p.hospitals }))} />
            <LayerToggle label="Vehicles" color="#06b6d4" count={vehicles.length} active={layers.vehicles} onClick={() => setLayers((p) => ({ ...p, vehicles: !p.vehicles }))} />
            <LayerToggle label="Incidents" color="#ef4444" count={incidents.length} active={layers.incidents} onClick={() => setLayers((p) => ({ ...p, incidents: !p.incidents }))} />
          </div>
        </div>

        {selected ? (
          <Inspector selected={selected} onClose={() => setSelected(null)} />
        ) : (
          <div className="rounded-xl border border-line/40 bg-surface/30 p-3 text-center text-[11px] text-ink-faint">
            Click a road, hospital, vehicle, or incident on the map to inspect it.
          </div>
        )}
      </div>

      <div ref={containerRef} className="relative flex-1 h-full" />
    </div>
  );
}

function mergeByKey<T>(initial: T[], live: Record<string, T>, keyOf: (item: T) => string): T[] {
  const merged = initial.map((item) => live[keyOf(item)] ?? item);
  const known = new Set(merged.map(keyOf));
  for (const [key, item] of Object.entries(live)) {
    if (!known.has(key)) merged.push(item);
  }
  return merged;
}

function LayerToggle({
  label, color, count, active, onClick,
}: {
  label: string;
  color: string;
  count: number;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center justify-between p-2 rounded-lg border text-left transition-all ${
        active ? "border-line bg-surface/70 text-ink" : "border-transparent bg-transparent text-ink-faint hover:text-ink-muted"
      }`}
    >
      <div className="flex items-center gap-2">
        <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: active ? color : "currentColor" }} />
        <span className="text-xs font-medium">{label}</span>
      </div>
      <span className="rounded-full bg-surface-muted px-1.5 py-0.2 text-[10px] font-mono text-ink-muted">{count}</span>
    </button>
  );
}

function Inspector({ selected, onClose }: { selected: Selected; onClose: () => void }) {
  return (
    <div className="rounded-xl border border-brand/40 bg-brand/5 p-3 space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-bold uppercase tracking-wider text-brand">Inspector · {selected.kind}</span>
        <button onClick={onClose} className="text-[10px] text-ink-muted hover:text-ink">✕</button>
      </div>
      {selected.kind === "road" && (
        <>
          <p className="text-xs font-semibold text-ink truncate">{selected.data.name}</p>
          <div className="text-[10px] space-y-1 text-ink-muted">
            <p>Traffic: <strong>{selected.data.traffic_level}</strong> · Risk: <strong>{selected.data.risk_level}</strong></p>
            <p>Vehicles: {selected.data.current_vehicle_count} / {selected.data.capacity}</p>
            <p>Avg speed: {selected.data.average_speed_kmh ?? "—"} km/h</p>
          </div>
        </>
      )}
      {selected.kind === "hospital" && (
        <>
          <p className="text-xs font-semibold text-ink truncate">{selected.data.name}</p>
          <div className="text-[10px] space-y-1 text-ink-muted">
            <p>Beds: {selected.data.beds_occupied} / {selected.data.beds_total}</p>
            <p>ICU: {selected.data.icu_occupied} / {selected.data.icu_total}</p>
            <p>Status: <strong>{selected.data.status}</strong></p>
          </div>
        </>
      )}
      {selected.kind === "vehicle" && (
        <>
          <p className="text-xs font-semibold text-ink truncate">{selected.data.vehicle_id}</p>
          <div className="text-[10px] space-y-1 text-ink-muted">
            <p>Type: <strong>{selected.data.vehicle_type}</strong></p>
            <p>Speed: {selected.data.speed_kmh ?? "—"} km/h</p>
            <p>Status: <strong>{selected.data.status}</strong></p>
          </div>
        </>
      )}
      {selected.kind === "incident" && (
        <>
          <p className="text-xs font-semibold text-ink truncate">{selected.data.incident_number}</p>
          <div className="text-[10px] space-y-1 text-ink-muted">
            <p>Severity: <strong>{selected.data.severity}</strong> · Status: <strong>{selected.data.status}</strong></p>
            <p className="line-clamp-2">{selected.data.description}</p>
            <p>
              Reported:{" "}
              <strong>
                {new Date(selected.data.created_at).toLocaleString(undefined, {
                  dateStyle: "medium",
                  timeStyle: "short",
                })}
              </strong>
            </p>
          </div>
          {selected.data.image_url && (
            // Evidence photo (spec section 16) -- synthetic providers use
            // picsum.photos placeholders (spec section 86: never pretend
            // simulated data is real), a real operator upload would point
            // here just the same.
            <img
              src={selected.data.image_url}
              alt={`Evidence for ${selected.data.incident_number}`}
              className="w-full rounded-lg border border-line/40 object-cover"
            />
          )}
        </>
      )}
    </div>
  );
}
