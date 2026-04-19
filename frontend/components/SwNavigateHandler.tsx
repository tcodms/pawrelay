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

      const openMatching = url.searchParams.get("openMatching");
      const chatMatch = url.pathname.match(/\/volunteer\/chat\/([^/]+)/);
      const chatSessionId = chatMatch?.[1];

      if (openMatching && chatSessionId && url.pathname.startsWith("/volunteer/chat/")) {
        sessionStorage.setItem("matchingChatSession", chatSessionId);
        router.push(`/volunteer/matching/${openMatching}`);
      } else {
        router.push(url.pathname + url.search);
      }
    }
    navigator.serviceWorker?.addEventListener("message", handleMessage);
    return () => navigator.serviceWorker?.removeEventListener("message", handleMessage);
  }, [router]);

  return null;
}
