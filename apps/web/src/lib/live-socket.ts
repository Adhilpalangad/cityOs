"use client";

import { useEffect, useRef, useState } from "react";
import { getAccessToken } from "./auth-client";
import type { Road, Vehicle } from "./city-api";
import { env } from "./env";

type RoadUpdateMessage = { type: "ROAD_UPDATE"; road: Road };
type VehicleUpdateMessage = { type: "VEHICLE_UPDATE"; vehicle: Vehicle };
type LiveMessage = RoadUpdateMessage | VehicleUpdateMessage;

export interface LiveFeedState {
  roads: Record<string, Road>;
  vehicles: Record<string, Vehicle>;
  connected: boolean;
}

const RECONNECT_DELAY_MS = 5000;

function liveFeedUrl(): string {
  return env.apiUrl.replace(/^http/, "ws") + "/ws/live";
}

/**
 * Subscribes to city-core's live Road/Vehicle feed, relayed through the
 * gateway (services/api-gateway/app/api/ws_proxy.py -> city-core's
 * app/api/routes_live.py). Reconnects on drop; callers merge the returned
 * maps onto their initial server-fetched snapshot, keyed by `code` /
 * `vehicle_id`, the same natural keys the backend upserts by.
 */
export function useLiveFeed(): LiveFeedState {
  const [roads, setRoads] = useState<Record<string, Road>>({});
  const [vehicles, setVehicles] = useState<Record<string, Vehicle>>({});
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

  return { roads, vehicles, connected };
}
