"use client";

import { createContext, useContext, useRef, useState } from "react";
import { AlertTriangle, AlertOctagon, Bell } from "lucide-react";
import { useWebSocket, type WsEventName, type WsPayloadMap } from "@/hooks/useWebSocket";
import type { AppNotification } from "@/lib/api/notifications";
import type { PingStatus } from "@/lib/dummy-posts";
export type { PingStatus };

interface WsToast {
  id: number;
  type: "delay" | "sos";
  message: string;
}

interface DashboardWsContextValue {
  pingStatusMap: Record<number, PingStatus>;
  unreadCount: number;
}

const DashboardWsContext = createContext<DashboardWsContextValue>({
  pingStatusMap: {},
  unreadCount: 0,
});

export function useDashboardWs() {
  return useContext(DashboardWsContext);
}

// ── 서브 컴포넌트 ─────────────────────────────────────────────────────────────

function UnreadBadge({ unreadCount }: { unreadCount: number }) {
  if (unreadCount === 0) return null;
  return (
    <div
      aria-label={`읽지 않은 알림 ${unreadCount}개`}
      className="fixed top-4 right-14 z-50 flex h-8 w-8 items-center justify-center rounded-full bg-white/80 backdrop-blur-sm border border-gray-200 shadow-sm"
    >
      <Bell size={15} className="text-gray-400" />
      <span className="absolute -top-1 -right-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-0.5 text-[9px] font-bold text-white">
        {unreadCount > 99 ? "99+" : unreadCount}
      </span>
    </div>
  );
}

function WsToastStack({ wsToasts }: { wsToasts: WsToast[] }) {
  return (
    <div
      aria-live="assertive"
      className="fixed bottom-8 left-1/2 -translate-x-1/2 z-[999999] flex flex-col items-center gap-2 pointer-events-none"
    >
      {wsToasts.map((t) => (
        <div
          key={t.id}
          role="alert"
          className="pointer-events-auto flex items-center gap-2.5 rounded-2xl bg-gray-100/95 px-5 py-3 shadow-lg text-[13px] font-medium text-gray-900 whitespace-nowrap"
        >
          {t.type === "sos"
            ? <AlertOctagon size={14} className="shrink-0 text-red-500" />
            : <AlertTriangle size={14} className="shrink-0 text-amber-500" />}
          {t.message}
        </div>
      ))}
    </div>
  );
}

// ── 상태 훅 ──────────────────────────────────────────────────────────────────

function useDashboardWsState() {
  const [pingStatusMap, setPingStatusMap] = useState<Record<number, PingStatus>>({});
  const [unreadCount, setUnreadCount] = useState(0);
  const [wsToasts, setWsToasts] = useState<WsToast[]>([]);
  const nextIdRef = useRef(0);

  function addToast(type: WsToast["type"], message: string) {
    const id = ++nextIdRef.current;
    setWsToasts((prev) => [...prev, { id, type, message }]);
    setTimeout(() => setWsToasts((prev) => prev.filter((t) => t.id !== id)), 5000);
  }

  function handleEvent<K extends WsEventName>(event: K, payload: WsPayloadMap[K]) {
    if (event === "ping.confirmed") {
      const { segment_id } = payload as WsPayloadMap["ping.confirmed"];
      setPingStatusMap((prev) => ({ ...prev, [segment_id]: "confirmed" }));
    } else if (event === "departure.no_response") {
      const { segment_id } = payload as WsPayloadMap["departure.no_response"];
      setPingStatusMap((prev) => ({ ...prev, [segment_id]: "departure_no_response" }));
    } else if (event === "handover.no_response") {
      const { segment_id } = payload as WsPayloadMap["handover.no_response"];
      setPingStatusMap((prev) => ({ ...prev, [segment_id]: "handover_no_response" }));
    } else if (event === "delay.reported") {
      addToast("delay", (payload as WsPayloadMap["delay.reported"]).message);
    } else if (event === "sos.triggered") {
      addToast("sos", "SOS! 긴급 재매칭 요청이 발생했습니다.");
    }
  }

  function handleUnread(notifications: AppNotification[]) {
    setUnreadCount(notifications.length);
  }

  useWebSocket({ onEvent: handleEvent, onUnreadNotifications: handleUnread });

  return { pingStatusMap, unreadCount, wsToasts };
}

// ── 프로바이더 ────────────────────────────────────────────────────────────────

export function DashboardWsProvider({ children }: { children: React.ReactNode }) {
  const { pingStatusMap, unreadCount, wsToasts } = useDashboardWsState();

  return (
    <DashboardWsContext.Provider value={{ pingStatusMap, unreadCount }}>
      <UnreadBadge unreadCount={unreadCount} />
      {children}
      <WsToastStack wsToasts={wsToasts} />
    </DashboardWsContext.Provider>
  );
}
