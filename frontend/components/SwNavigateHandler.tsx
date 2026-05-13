"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function SwNavigateHandler() {
  const router = useRouter();

  useEffect(() => {
    function handleMessage(e: MessageEvent) {
      if (!e.data || e.data.type !== "SW_NAVIGATE") return;
      if (typeof e.data.url !== "string") return;

      let url: URL;
      try {
        url = new URL(e.data.url, window.location.origin);
      } catch {
        return;
      }

      if (url.origin !== window.location.origin) return;

      router.push(url.pathname + url.search);
    }
    navigator.serviceWorker?.addEventListener("message", handleMessage);
    return () => navigator.serviceWorker?.removeEventListener("message", handleMessage);
  }, [router]);

  return null;
}
