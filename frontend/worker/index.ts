export {};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const sw = self as any;

// ── Web Push 수신 ─────────────────────────────────────────────────────────────

sw.addEventListener("push", (event: any) => {
  if (!event.data) return;

  const data = event.data.json() as {
    message: string;
    url?: string;
    type?: string;
  };

  event.waitUntil(
    sw.registration.showNotification("PawRelay 🐾", {
      body: data.message,
      icon: "/icons/icon-192x192.svg",
      badge: "/icons/icon-192x192.svg",
      data: { url: data.url ?? "/volunteer" },
      vibrate: [200, 100, 200],
    })
  );
});

// ── 알림 클릭 → 해당 페이지로 이동 ──────────────────────────────────────────

sw.addEventListener("notificationclick", (event: any) => {
  event.notification.close();

  const url: string = event.notification.data?.url ?? "/volunteer";

  event.waitUntil(
    sw.clients
      .matchAll({ type: "window", includeUncontrolled: true })
      .then((clients: any[]) => {
        for (const client of clients) {
          if ("navigate" in client) {
            return (client as any).focus().then((c: any) => c.navigate(url));
          }
        }
        return sw.clients.openWindow(url);
      })
  );
});
