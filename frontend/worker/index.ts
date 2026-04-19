export {};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const sw = self as any;

// ── Web Push 수신 ─────────────────────────────────────────────────────────────

sw.addEventListener("push", (event: any) => {
  if (!event.data) return;

  const data = event.data.json() as {
    type?: string;
    message: string;
    url?: string;
    segment_id?: number;
    chat_session_id?: string;
  };

  // 앱이 열려 있으면 채팅방에 postMessage로 버블 추가 요청
  const MATCHING_TYPES = ["matching_proposed", "matching_confirmed", "ping_check"];
  if (data.type && MATCHING_TYPES.includes(data.type)) {
    sw.clients.matchAll({ type: "window", includeUncontrolled: true }).then((clients: any[]) => {
      clients.forEach((client: any) => client.postMessage({ type: "PUSH_NOTIFICATION", payload: data }));
    });
  }

  event.waitUntil(
    sw.registration.showNotification("PawRelay 🐾", {
      body: data.message,
      icon: "/icons/icon-192x192.svg",
      badge: "/icons/icon-192x192.svg",
      data: { url: data.url ?? "/volunteer", chat_session_id: data.chat_session_id },
      vibrate: [200, 100, 200],
    })
  );
});

// ── 알림 클릭 → 해당 페이지로 이동 ──────────────────────────────────────────

sw.addEventListener("notificationclick", (event: any) => {
  event.notification.close();

  const { url, chat_session_id } = event.notification.data ?? {};
  const segmentMatch = (url ?? "").match(/\/volunteer\/matching\/(\d+)/);
  const segmentId = segmentMatch?.[1];

  // chat_session_id + segment_id 있으면 채팅방 먼저 열고 매칭 상세로 자동 이동
  const destination =
    chat_session_id && segmentId
      ? `/volunteer/chat/${chat_session_id}?openMatching=${segmentId}`
      : (url ?? "/volunteer");

  event.waitUntil(
    sw.clients
      .matchAll({ type: "window", includeUncontrolled: true })
      .then((clients: any[]) => {
        if (clients.length > 0) {
          clients.forEach((c: any) => c.postMessage({ type: "SW_NAVIGATE", url: destination }));
          return clients[0].focus();
        }
        return sw.clients.openWindow(destination);
      })
  );
});
