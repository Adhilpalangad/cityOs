"use client";

import { useEffect, useRef, useState } from "react";
import { getAccessToken } from "./auth-client";
import type { Incident, Road, Vehicle } from "./city-api";
import { env } from "./env";

type RoadUpdateMessage = { type: "ROAD_UPDATE"; road: Road };
type VehicleUpdateMessage = { type: "VEHICLE_UPDATE"; vehicle: Vehicle };
type IncidentUpdateMessage = { type: "INCIDENT_UPDATE"; incident: Incident };
type LiveMessage = RoadUpdateMessage | VehicleUpdateMessage | IncidentUpdateMessage;

export interface LiveFeedState {
  roads: Record<string, Road>;
  vehicles: Record<string, Vehicle>;
  incidents: Record<string, Incident>;
  connected: boolean;
}

const RECONNECT_DELAY_MS = 5000;

function liveFeedUrl(): string {
  return env.apiUrl.replace(/^http/, "ws") + "/ws/live";
}

/**
 * Subscribes to city-core's live Road/Vehicle/Incident feed, relayed
 * through the gateway (services/api-gateway/app/api/ws_proxy.py ->
 * city-core's app/api/routes_live.py). Reconnects on drop; callers merge
 * `roads`/`vehicles` onto their initial server-fetched snapshot keyed by
 * `code`/`vehicle_id` (the natural keys the backend upserts by).
 * `incidents` is keyed by row id instead -- every incident event is a new
 * row (see app/services/live_ingest.py's apply_incident_event), so there's
 * no natural key to upsert against; callers append rather than merge.
 */
export function useLiveFeed(): LiveFeedState {
  const [roads, setRoads] = useState<Record<string, Road>>({});
  const [vehicles, setVehicles] = useState<Record<string, Vehicle>>({});
  const [incidents, setIncidents] = useState<Record<string, Incident>>({});
  const [connected, setConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let cancelled = false;
    let retryTimer: ReturnType<typeof setTimeout> | undefined;

    function connect() {
      const token = getAccessToken();
      if (!token || cancelled) return;

      const socket = new WebSocket(`${liveFeedUrl()}?token=${encodeURIComponent(token)}`);
      socketRef.current = socket;

      socket.onopen = () => setConnected(true);
      socket.onerror = () => socket.close();
      socket.onclose = () => {
        setConnected(false);
        if (!cancelled) retryTimer = setTimeout(connect, RECONNECT_DELAY_MS);
      };
      socket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as LiveMessage;
          if (message.type === "ROAD_UPDATE") {
            setRoads((prev) => ({ ...prev, [message.road.code]: message.road }));
          } else if (message.type === "VEHICLE_UPDATE") {
            setVehicles((prev) => ({ ...prev, [message.vehicle.vehicle_id]: message.vehicle }));
          } else if (message.type === "INCIDENT_UPDATE") {
            setIncidents((prev) => ({ ...prev, [message.incident.id]: message.incident }));
          }
        } catch {
          // Malformed frame -- drop it rather than tearing down the socket.
        }
      };
    }

    connect();
    return () => {
      cancelled = true;
      clearTimeout(retryTimer);
      socketRef.current?.close();
    };
  }, []);

  return { roads, vehicles, incidents, connected };
}
