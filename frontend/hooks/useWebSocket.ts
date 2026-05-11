"use client";

import { useEffect, useRef } from "react";
import { getUnreadNotifications, type AppNotification } from "@/lib/api/notifications";

export type WsEventName =
  | "checkpoint.updated"
  | "ping.confirmed"
  | "ping.no_response"
  | "delay.reported"
  | "sos.triggered";

export interface WsPayloadMap {
  "checkpoint.updated": {
    transport_post_id: number;
    segment_order: number;
    latitude: number | null;
    longitude: number | null;
    recorded_at: string;
  };
  "ping.confirmed": { segment_id: number; volunteer_name: string };
  "ping.no_response": { segment_id: number; volunteer_name: string; scheduled_time: string };
  "delay.reported": { segment_id: number; message: string };
  "sos.triggered": { segment_id: number; latitude: number | null; longitude: number | null };
}

type WsMessage = {
  [K in WsEventName]: { event: K; payload: WsPayloadMap[K] };
}[WsEventName];

export interface UseWebSocketOptions {
  shareToken?: string;
  onEvent?: <K extends WsEventName>(eventName: K, payload: WsPayloadMap[K]) => void;
  onUnreadNotifications?: (notifications: AppNotification[]) => void;
  enabled?: boolean;
}

const MAX_DELAY_MS = 30_000;
const BASE_DELAY_MS = 1_000;

const VALID_WS_EVENTS = new Set<WsEventName>([
  "checkpoint.updated",
  "ping.confirmed",
  "ping.no_response",
  "delay.reported",
  "sos.triggered",
]);

function buildWsUrl(shareToken?: string): string {
  const base = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";
  return shareToken ? `${base}/ws?share_token=${shareToken}` : `${base}/ws`;
}

export function useWebSocket({
  shareToken,
  onEvent,
  onUnreadNotifications,
  enabled = true,
}: UseWebSocketOptions = {}) {
  // Callbacks in refs → effect doesn't re-run on callback reference changes
  const onEventRef = useRef(onEvent);
  const onUnreadRef = useRef(onUnreadNotifications);
  useEffect(() => { onEventRef.current = onEvent; }, [onEvent]);
  useEffect(() => { onUnreadRef.current = onUnreadNotifications; }, [onUnreadNotifications]);

  useEffect(() => {
    if (!enabled) return;

    let ws: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let reconnectDelay = BASE_DELAY_MS;
    let active = true;

    function connect() {
      if (!active) return;

      ws = new WebSocket(buildWsUrl(shareToken));

      ws.onopen = () => {
        reconnectDelay = BASE_DELAY_MS;
        // share_token users are unauthenticated — skip the notifications fetch
        if (!shareToken) {
          getUnreadNotifications()
            .then((notifications) => onUnreadRef.current?.(notifications))
            .catch(() => {});
        }
      };

      ws.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data as string);
          if (
            typeof parsed?.event !== "string" ||
            !VALID_WS_EVENTS.has(parsed.event as WsEventName) ||
            parsed.payload === undefined
          ) return;
          onEventRef.current?.(parsed.event as WsEventName, parsed.payload);
        } catch {}
      };

      ws.onclose = () => {
        if (!active) return;
        const delay = reconnectDelay;
        reconnectDelay = Math.min(reconnectDelay * 2, MAX_DELAY_MS);
        reconnectTimer = setTimeout(connect, delay);
      };

      ws.onerror = () => {
        ws?.close();
      };
    }

    connect();

    return () => {
      active = false;
      if (reconnectTimer !== null) clearTimeout(reconnectTimer);
      ws?.close();
    };
  }, [shareToken, enabled]);
}
