/**
 * beforeinstallprompt 이벤트는 페이지 초기 로드 직후 한 번만 발생합니다.
 * 컴포넌트 마운트 전에 이미 발생할 수 있으므로 모듈 로드 시점에 즉시 등록합니다.
 */

import { request } from "@/lib/api";

export interface BeforeInstallPromptEvent extends Event {
  prompt(): Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

let _deferredPrompt: BeforeInstallPromptEvent | null = null;

// 모듈 로드 시 즉시 등록 — initPwaPromptCapture() 호출 타이밍에 무관하게 캡처
if (typeof window !== "undefined") {
  window.addEventListener("beforeinstallprompt", (e) => {
    _deferredPrompt = e as BeforeInstallPromptEvent;
  });
}

/** @deprecated 모듈 로드 시 자동 등록되므로 호출 불필요. 하위 호환성을 위해 유지. */
export function initPwaPromptCapture(): void {}

export function getDeferredInstallPrompt(): BeforeInstallPromptEvent | null {
  return _deferredPrompt;
}

export function clearDeferredInstallPrompt(): void {
  _deferredPrompt = null;
}

// ── 플랫폼 감지 ──────────────────────────────────────────────────────────────

export function isIos(): boolean {
  return /iPad|iPhone|iPod/.test(navigator.userAgent);
}

export function isStandalone(): boolean {
  return (
    window.matchMedia("(display-mode: standalone)").matches ||
    ("standalone" in navigator && (navigator as { standalone: boolean }).standalone === true)
  );
}

/** iOS + Safari (CriOS/FxiOS 등 제외) */
export function isIosSafari(): boolean {
  const ua = navigator.userAgent;
  return /iPad|iPhone|iPod/.test(ua) && !/CriOS|FxiOS|OPiOS|mercury/.test(ua);
}

// ── Web Push 구독 ─────────────────────────────────────────────────────────────

function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; i++) outputArray[i] = rawData.charCodeAt(i);
  return outputArray;
}

async function getVapidKey(): Promise<string> {
  const res = await request<{ public_key: string }>("/notifications/push/vapid-key");
  return res.public_key;
}

export async function subscribePush(): Promise<void> {
  if (!("serviceWorker" in navigator) || !("PushManager" in window)) return;
  const registration = await navigator.serviceWorker.ready;
  const existing = await registration.pushManager.getSubscription();
  if (existing) return;
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
