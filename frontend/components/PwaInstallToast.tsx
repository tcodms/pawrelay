"use client";

import { useEffect, useState } from "react";
import {
  getDeferredInstallPrompt,
  clearDeferredInstallPrompt,
  BeforeInstallPromptEvent,
} from "@/lib/pwa";

const DISMISSED_KEY = "pwa_toast_dismissed";

function shouldShow(): boolean {
  if (typeof window === "undefined") return false;
  const isStandalone =
    window.matchMedia("(display-mode: standalone)").matches ||
    ("standalone" in navigator &&
      (navigator as { standalone: boolean }).standalone === true);
  if (isStandalone) return false;
  if (localStorage.getItem(DISMISSED_KEY)) return false;
  return /iPad|iPhone|iPod|Android/.test(navigator.userAgent);
}

export default function PwaInstallToast() {
  const [visible, setVisible] = useState(false);
  const [installing, setInstalling] = useState(false);
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);

  useEffect(() => {
    if (!shouldShow()) return;
    setDeferredPrompt(getDeferredInstallPrompt());
    setVisible(true);
  }, []);

  useEffect(() => {
    function handlePrompt(e: Event) {
      setDeferredPrompt(e as BeforeInstallPromptEvent);
    }
    window.addEventListener("beforeinstallprompt", handlePrompt);
    return () => window.removeEventListener("beforeinstallprompt", handlePrompt);
  }, []);

  function handleDismiss() {
    localStorage.setItem(DISMISSED_KEY, "1");
    setVisible(false);
  }

  async function handleInstall() {
    if (!deferredPrompt) return;
    setInstalling(true);
    try {
      await deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      clearDeferredInstallPrompt();
      setDeferredPrompt(null);
      if (outcome === "accepted") {
        localStorage.setItem(DISMISSED_KEY, "1");
        setVisible(false);
      }
    } finally {
      setInstalling(false);
    }
  }

  if (!visible) return null;

  return (
    <div
      role="banner"
      className="fixed top-0 inset-x-0 z-50 flex items-center gap-3 bg-[#EEA968] px-4 py-3 shadow-md animate-fade-in"
    >
      {/* 앱 아이콘 */}
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-white/20">
        <svg
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="white"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <ellipse cx="12" cy="17" rx="4" ry="3" />
          <ellipse cx="7.5" cy="12" rx="1.5" ry="2" />
          <ellipse cx="16.5" cy="12" rx="1.5" ry="2" />
          <ellipse cx="9" cy="8.5" rx="1.3" ry="1.8" />
          <ellipse cx="15" cy="8.5" rx="1.3" ry="1.8" />
        </svg>
      </div>

      <p className="flex-1 text-[13px] font-semibold text-white leading-snug">
        PawRelay 앱으로 더 빠르게 매칭을 받아보세요!
      </p>

      {deferredPrompt && (
        <button
          type="button"
          onClick={handleInstall}
          disabled={installing}
          className="shrink-0 rounded-xl bg-white px-3.5 py-1.5 text-[12px] font-bold text-[#EEA968] transition-all active:scale-95 disabled:opacity-60"
        >
          {installing ? "설치 중" : "설치"}
        </button>
      )}

      <button
        type="button"
        onClick={handleDismiss}
        aria-label="닫기"
        className="shrink-0 text-white/80 hover:text-white transition-colors"
      >
        <svg
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
        >
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>
    </div>
  );
}
