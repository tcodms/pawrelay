"use client";

import { useEffect } from "react";
import { request } from "@/lib/api";

async function getVapidKey(): Promise<string> {
  const res = await request<{ public_key: string }>("/notifications/push/vapid-key");
  return res.public_key;
}

function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; i++) outputArray[i] = rawData.charCodeAt(i);
  return outputArray;
}

async function subscribePush() {
  if (!("serviceWorker" in navigator) || !("PushManager" in window)) return;

  const registration = await navigator.serviceWorker.ready;
  const existing = await registration.pushManager.getSubscription();
  if (existing) return; // 이미 구독 중

  const vapidKey = await getVapidKey();
  const subscription = await registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(vapidKey).buffer as ArrayBuffer,
  });

  const { endpoint, keys } = subscription.toJSON() as {
    endpoint: string;
    keys: { p256dh: string; auth: string };
  };

  await request("/notifications/push/subscribe", {
    method: "POST",
    body: JSON.stringify({ endpoint, keys }),
  });
}

export default function NotificationPermission() {
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (!("Notification" in window)) return;

    if (Notification.permission === "granted") {
      subscribePush().catch(() => {});
      return;
    }

    if (Notification.permission === "default") {
      Notification.requestPermission().then((result) => {
        if (result === "granted") subscribePush().catch(() => {});
      });
    }
  }, []);

  return null;
}
