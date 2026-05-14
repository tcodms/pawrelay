"use client";

import { useEffect, useRef, useState } from "react";
import {
  getDeferredInstallPrompt,
  clearDeferredInstallPrompt,
  BeforeInstallPromptEvent,
  isStandalone,
  subscribePush,
} from "@/lib/pwa";

type Platform = "ios-safari" | "ios-other" | "android" | "other";

function detectPlatform(): Platform {
  const ua = navigator.userAgent;
  if (/iPad|iPhone|iPod/.test(ua)) {
    return /CriOS|FxiOS|OPiOS|mercury/.test(ua) ? "ios-other" : "ios-safari";
  }
  if (/Android/.test(ua)) return "android";
  return "other";
}

const IOS_STEPS = [
  "하단 공유 버튼 ( ↑ ) 탭하기",
  '"홈 화면에 추가" 선택하기',
  '오른쪽 위 "추가" 탭하기',
];

const ANDROID_STEPS = [
  "브라우저 상단 메뉴 ( ⋮ ) 탭하기",
  '"홈 화면에 추가" 선택하기',
];

function StepList({ steps }: { steps: string[] }) {
  return (
    <div className="flex flex-col gap-3">
      {steps.map((text, i) => (
        <div key={i} className="flex items-center gap-3">
          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#FDF3EC] text-[11px] font-bold text-[#EEA968]">
            {i + 1}
          </span>
          <p className="text-[14px] text-gray-600 leading-snug">{text}</p>
        </div>
      ))}
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
    if (isStandalone()) { onDismissRef.current(); return; }
    const detected = detectPlatform();
    setPlatform(detected);
    if (detected === "other") onDismissRef.current();
  }, []);

  async function handleInstall() {
    if (!deferredPrompt) return;
    setInstalling(true);
    try {
      await deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      clearDeferredInstallPrompt();
      setDeferredPrompt(null);
      if (outcome === "accepted") handleDismiss();
    } finally {
      setInstalling(false);
    }
  }

  function handleDismiss() {
    if (isStandalone()) subscribePush().catch(() => {});
    onDismissRef.current();
  }

  if (!platform || platform === "other") return null;

  return (
    <>
      {/* 배경 */}
      <div className="fixed inset-0 z-[9998] bg-black/40 backdrop-blur-sm" onClick={handleDismiss} />

      {/* 바텀 시트 */}
      <div className="fixed bottom-0 inset-x-0 z-[9999] mx-auto max-w-lg rounded-t-3xl bg-white px-6 pt-4 pb-10 shadow-2xl">
        {/* 핸들 */}
        <div className="mb-6 flex justify-center">
          <div className="h-1 w-10 rounded-full bg-gray-200" />
        </div>

        {/* 앱 헤더 */}
        <div className="mb-6 flex items-center gap-3.5">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-[#EEA968] shadow-md shadow-[#EEA968]/20">
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
              <ellipse cx="12" cy="17" rx="4" ry="3" />
              <ellipse cx="7.5" cy="12" rx="1.5" ry="2" />
              <ellipse cx="16.5" cy="12" rx="1.5" ry="2" />
              <ellipse cx="9" cy="8.5" rx="1.3" ry="1.8" />
              <ellipse cx="15" cy="8.5" rx="1.3" ry="1.8" />
            </svg>
          </div>
          <div>
            <p className="text-[16px] font-bold text-gray-900 leading-tight">PawRelay 앱 설치</p>
            <p className="text-[12px] text-gray-400 mt-0.5">
              {platform === "ios-other"
                ? "Safari에서만 설치 가능합니다"
                : "홈 화면 추가 시 알림 수신이 가능해요"}
            </p>
          </div>
        </div>

        {/* 내용 */}
        {platform === "ios-safari" ? (
          <>
            <StepList steps={IOS_STEPS} />
            <p className="mt-4 text-center text-[11px] text-gray-300">iOS 16.4 이상 + Safari 전용</p>
          </>
        ) : platform === "ios-other" ? (
          <div className="rounded-2xl bg-amber-50 px-4 py-4 text-center">
            <p className="text-[13px] leading-relaxed text-gray-500">
              현재 브라우저에서는 설치 불가합니다.<br />
              <span className="font-semibold text-gray-700">Safari</span>로 다시 열기.
            </p>
          </div>
        ) : deferredPrompt ? (
          <button
            type="button"
            onClick={handleInstall}
            disabled={installing}
            className="h-13 w-full rounded-2xl bg-[#EEA968] text-[15px] font-bold text-white shadow-md shadow-[#EEA968]/20 transition-all active:scale-[0.97] disabled:bg-gray-100 disabled:text-gray-400"
          >
            {installing ? "설치 중..." : "홈 화면에 설치하기"}
          </button>
        ) : (
          <StepList steps={ANDROID_STEPS} />
        )}

        {/* 닫기 */}
        <button
          type="button"
          onClick={handleDismiss}
          className="mt-6 w-full text-center text-[13px] text-gray-400 hover:text-gray-600 transition-colors"
        >
          나중에 하기
        </button>
      </div>
    </>
  );
}
