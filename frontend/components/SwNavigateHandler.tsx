"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function SwNavigateHandler() {
  const router = useRouter();

  useEffect(() => {
    function handleMessage(e: MessageEvent) {
      if (e.data?.type !== "SW_NAVIGATE") return;
      const url = new URL(e.data.url, window.location.origin);
      const openMatching = url.searchParams.get("openMatching");
      const chatMatch = url.pathname.match(/\/volunteer\/chat\/([^/]+)/);
      const chatSessionId = chatMatch?.[1];

      if (openMatching && chatSessionId) {
        sessionStorage.setItem("matchingChatSession", chatSessionId);
        router.push(`/volunteer/matching/${openMatching}`);
      } else {
        router.push(e.data.url);
      }
    }
    navigator.serviceWorker?.addEventListener("message", handleMessage);
    return () => navigator.serviceWorker?.removeEventListener("message", handleMessage);
  }, [router]);

  return null;
}
