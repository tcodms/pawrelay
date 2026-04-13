"use client";

import { useEffect, useRef, useState } from "react";
import {
  getDeferredInstallPrompt,
  clearDeferredInstallPrompt,
  BeforeInstallPromptEvent,
} from "@/lib/pwa";

type Platform = "ios" | "android" | "other";

function detectPlatform(): Platform {
  const ua = navigator.userAgent;
  if (/iPad|iPhone|iPod/.test(ua)) return "ios";
  if (/Android/.test(ua)) return "android";
  return "other";
}

function isStandalone(): boolean {
  return (
    window.matchMedia("(display-mode: standalone)").matches ||
    ("standalone" in navigator &&
      (navigator as { standalone: boolean }).standalone === true)
  );
}

function StepRow({ icon, text }: { icon: React.ReactNode; text: string }) {
  return (
    <div className="flex items-center gap-4 rounded-2xl bg-orange-50 px-4 py-3.5">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white shadow-sm">
        {icon}
      </div>
      <p className="text-[14px] leading-snug text-gray-700">{text}</p>
    </div>
  );
}

interface Props {
  onDismiss: () => void;
}

export default function PwaInstallModal({ onDismiss }: Props) {
  const [platform, setPlatform] = useState<Platform | null>(null);
  const [installing, setInstalling] = useState(false);
  const [deferredPrompt, setDeferredPrompt] = useState(getDeferredInstallPrompt);
  const onDismissRef = useRef(onDismiss);
  useEffect(() => { onDismissRef.current = onDismiss; }, [onDismiss]);

  useEffect(() => {
    function handlePrompt(e: Event) {
      setDeferredPrompt(e as BeforeInstallPromptEvent);
    }
    window.addEventListener("beforeinstallprompt", handlePrompt);
    return () => window.removeEventListener("beforeinstallprompt", handlePrompt);
  }, []);

  useEffect(() => {
    if (isStandalone()) {
      onDismissRef.current();
      return;
    }
    const detected = detectPlatform();
    setPlatform(detected);
    if (detected === "other") {
      onDismissRef.current();
    }
  }, []);

  async function handleInstall() {
    if (!deferredPrompt) return;
    setInstalling(true);
    try {
      await deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      clearDeferredInstallPrompt();
      setDeferredPrompt(null);
      if (outcome === "accepted") onDismissRef.current();
    } finally {
      setInstalling(false);
    }
  }

  if (!platform || platform === "other") return null;

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-white px-6 py-12">
      {/* 앱 아이콘 */}
      <div className="mb-6 flex flex-col items-center gap-3 animate-scale-in">
        <div className="flex h-24 w-24 items-center justify-center rounded-[32px] bg-orange-500 shadow-xl shadow-orange-200">
          <svg
            width="52"
            height="52"
            viewBox="0 0 24 24"
            fill="none"
            stroke="white"
            strokeWidth="1.5"
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
        <p className="text-[13px] font-bold text-orange-500">PawRelay</p>
      </div>

      <div
        className="w-full max-w-sm animate-slide-up"
        style={{ animationDelay: "0.1s" }}
      >
        {/* 환영 문구 */}
        <div className="mb-7 text-center">
          <p className="text-[22px] font-bold text-gray-900">가입을 환영합니다! 🐾</p>
          <p className="mt-2 text-[14px] leading-relaxed text-gray-500">
            앱을 설치하면 봉사 공고를
            <br />
            훨씬 편하게 확인할 수 있어요.
          </p>
        </div>

        {/* OS별 안내 */}
        {platform === "ios" ? (
          <>
            <div className="flex flex-col gap-2.5 mb-7">
              <StepRow
                icon={
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#F97316" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8" />
                    <polyline points="16 6 12 2 8 6" />
                    <line x1="12" y1="2" x2="12" y2="15" />
                  </svg>
                }
                text="하단 툴바의 공유 버튼( ↑ )을 탭하세요"
              />
              <StepRow
                icon={
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#F97316" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="3" y="3" width="18" height="18" rx="3" />
                    <line x1="12" y1="8" x2="12" y2="16" />
                    <line x1="8" y1="12" x2="16" y2="12" />
                  </svg>
                }
                text='"홈 화면에 추가"를 선택하세요'
              />
              <StepRow
                icon={
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#F97316" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                }
                text='오른쪽 위 "추가"를 탭하면 완료예요!'
              />
            </div>
            <p className="text-center text-[11px] text-gray-400 mb-5">
              iOS 16.4 이상 + Safari에서만 지원됩니다.
            </p>
          </>
        ) : deferredPrompt ? (
          <button
            type="button"
            onClick={handleInstall}
            disabled={installing}
            className="h-14 w-full rounded-2xl bg-orange-500 text-[15px] font-bold text-white shadow-md shadow-orange-100 transition-all duration-150 active:scale-[0.97] disabled:bg-gray-100 disabled:text-gray-400 disabled:shadow-none mb-5"
          >
            {installing ? "설치 중..." : "홈 화면에 설치하기"}
          </button>
        ) : (
          <div className="flex flex-col gap-2.5 mb-7">
            <StepRow
              icon={
                <svg width="20" height="20" viewBox="0 0 24 24" fill="#F97316">
                  <circle cx="12" cy="5" r="1.8" />
                  <circle cx="12" cy="12" r="1.8" />
                  <circle cx="12" cy="19" r="1.8" />
                </svg>
              }
              text="브라우저 오른쪽 상단 메뉴( ⋮ )를 탭하세요"
            />
            <StepRow
              icon={
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#F97316" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="3" width="18" height="18" rx="3" />
                  <line x1="12" y1="8" x2="12" y2="16" />
                  <line x1="8" y1="12" x2="16" y2="12" />
                </svg>
              }
              text='"홈 화면에 추가"를 선택하세요'
            />
          </div>
        )}

        <button
          type="button"
          onClick={onDismiss}
          className="w-full rounded-2xl border border-gray-200 py-3.5 text-[14px] font-semibold text-gray-500 transition-colors active:bg-gray-50"
        >
          나중에 하기
        </button>
      </div>
    </main>
  );
}
