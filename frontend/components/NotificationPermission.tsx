"use client";

import { useEffect } from "react";
import { isIos, isStandalone, subscribePush } from "@/lib/pwa";

export default function NotificationPermission() {
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (!("Notification" in window)) return;
    // iOS는 PWA 설치(standalone) 후에만 Push 권한 획득 가능
    if (isIos() && !isStandalone()) return;

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
