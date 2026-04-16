"use client";

import { useEffect, useRef, useState } from "react";
import { getDeferredInstallPrompt, clearDeferredInstallPrompt, BeforeInstallPromptEvent } from "@/lib/pwa";

type Platform = "ios" | "android" | "other";

function detectPlatform(): Platform {
  const ua = navigator.userAgent;
  if (/iPad|iPhone|iPod/.test(ua)) return "ios";
  if (/Android/.test(ua)) return "android";
  return "other";
}

function isAlreadyInstalled(): boolean {
  return (
    window.matchMedia("(display-mode: standalone)").matches ||
    ("standalone" in navigator && (navigator as { standalone: boolean }).standalone === true)
  );
}

interface Props {
  onDismiss: () => void;
}

// ── 공통 아이콘 ───────────────────────────────────────────────────────────────

function StepRow({ icon, text }: { icon: React.ReactNode; text: string }) {
  return (
    <div className="flex items-center gap-4 rounded-2xl bg-gray-50 px-4 py-3.5">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white shadow-sm">
        {icon}
      </div>
      <p className="text-[14px] leading-snug text-gray-700">{text}</p>
    </div>
  );
}

// ── iOS 안내 ──────────────────────────────────────────────────────────────────

function IosGuide({ onDismiss }: { onDismiss: () => void }) {
  return (
    <>
      <div className="mb-6 text-center">
        <p className="text-[17px] font-bold text-gray-900">홈 화면에 추가하기</p>
        <p className="mt-1.5 text-[13px] leading-relaxed text-gray-500">
          Safari에서 홈 화면에 추가하면<br />
          앱처럼 알림을 받을 수 있어요.
        </p>
      </div>

      <div className="flex flex-col gap-2.5 mb-7">
        <StepRow
          icon={
            // iOS 공유 버튼 아이콘
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
            // 홈 화면 추가 아이콘
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

      <div className="space-y-3">
        <p className="text-center text-[11px] text-gray-400">
          iOS 16.4 이상 + Safari에서만 지원됩니다.
        </p>
        <button type="button" onClick={onDismiss}
          className="w-full rounded-2xl border border-gray-200 py-3.5 text-[14px] font-semibold text-gray-500 transition-colors active:bg-gray-50">
          나중에 하기
        </button>
      </div>
    </>
  );
}

// ── Android 안내 ──────────────────────────────────────────────────────────────

function AndroidGuide({ onDismiss }: { onDismiss: () => void }) {
  const [installing, setInstalling] = useState(false);
  const [deferredPrompt, setDeferredPrompt] = useState(getDeferredInstallPrompt);

  useEffect(() => {
    function handlePrompt(e: Event) {
      setDeferredPrompt(e as BeforeInstallPromptEvent);
    }
    window.addEventListener("beforeinstallprompt", handlePrompt);
    return () => window.removeEventListener("beforeinstallprompt", handlePrompt);
  }, []);

  async function handleInstall() {
    if (!deferredPrompt) return;
    setInstalling(true);
    try {
      await deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      clearDeferredInstallPrompt();
      setDeferredPrompt(null);
      if (outcome === "accepted") {
        onDismiss();
      }
    } finally {
      setInstalling(false);
    }
  }

  if (deferredPrompt) {
    return (
      <>
        <div className="mb-6 text-center">
          <p className="text-[17px] font-bold text-gray-900">앱으로 설치하기</p>
          <p className="mt-1.5 text-[13px] leading-relaxed text-gray-500">
            홈 화면에 설치하면 더 빠르게 열리고<br />
            이동 알림을 놓치지 않아요.
          </p>
        </div>

        <div className="mb-7">
          <button type="button" onClick={handleInstall} disabled={installing}
            className="h-14 w-full rounded-2xl bg-[#EEA968] text-[15px] font-bold text-white shadow-md shadow-[#EEA968]/20 transition-all duration-150 active:scale-[0.97] disabled:bg-gray-100 disabled:text-gray-400">
            {installing ? "설치 중..." : "홈 화면에 설치하기"}
          </button>
        </div>

        <button type="button" onClick={onDismiss}
          className="w-full rounded-2xl border border-gray-200 py-3.5 text-[14px] font-semibold text-gray-500 transition-colors active:bg-gray-50">
          나중에 하기
        </button>
      </>
    );
  }

  // beforeinstallprompt 이벤트를 놓쳤을 경우 수동 안내
  return (
    <>
      <div className="mb-6 text-center">
        <p className="text-[17px] font-bold text-gray-900">홈 화면에 추가하기</p>
        <p className="mt-1.5 text-[13px] leading-relaxed text-gray-500">
          홈 화면에 추가하면 앱처럼<br />
          이동 알림을 받을 수 있어요.
        </p>
      </div>

      <div className="flex flex-col gap-2.5 mb-7">
        <StepRow
          icon={
            // 세로 점 세 개 (브라우저 메뉴)
            <svg width="20" height="20" viewBox="0 0 24 24" fill="#F97316">
              <circle cx="12" cy="5" r="1.8" /><circle cx="12" cy="12" r="1.8" /><circle cx="12" cy="19" r="1.8" />
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

      <button type="button" onClick={onDismiss}
        className="w-full rounded-2xl border border-gray-200 py-3.5 text-[14px] font-semibold text-gray-500 transition-colors active:bg-gray-50">
        나중에 하기
      </button>
    </>
  );
}

// ── 메인 컴포넌트 ─────────────────────────────────────────────────────────────

export default function PwaInstallPrompt({ onDismiss }: Props) {
  const [platform, setPlatform] = useState<Platform | null>(null);
  // onDismiss를 ref로 보관해 useEffect dependency 없이 항상 최신 참조를 사용
  const onDismissRef = useRef(onDismiss);
  useEffect(() => { onDismissRef.current = onDismiss; }, [onDismiss]);

  useEffect(() => {
    // 이미 standalone(설치된 앱)으로 실행 중이면 바로 진행
    if (isAlreadyInstalled()) {
      onDismissRef.current();
      return;
    }

    const detected = detectPlatform();
    setPlatform(detected);

    // 데스크탑이면 안내 없이 바로 진행
    if (detected === "other") {
      onDismissRef.current();
    }
  }, []);

  // 플랫폼 감지 전, 또는 데스크탑이면 아무것도 렌더링하지 않음
  if (!platform || platform === "other") return null;

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-white px-6 py-12">
      {/* 상단 아이콘 */}
      <div className="mb-8 flex flex-col items-center gap-3 animate-scale-in">
        <div className="flex h-20 w-20 items-center justify-center rounded-[28px] bg-[#EEA968] shadow-lg shadow-[#EEA968]/25">
          <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            {/* 발바닥 아이콘 */}
            <ellipse cx="12" cy="17" rx="4" ry="3" />
            <ellipse cx="7.5" cy="12" rx="1.5" ry="2" />
            <ellipse cx="16.5" cy="12" rx="1.5" ry="2" />
            <ellipse cx="9" cy="8.5" rx="1.3" ry="1.8" />
            <ellipse cx="15" cy="8.5" rx="1.3" ry="1.8" />
          </svg>
        </div>
        <p className="text-[13px] font-semibold text-[#EEA968]">PawRelay</p>
      </div>

      {/* OS별 안내 */}
      <div className="w-full max-w-sm animate-slide-up" style={{ animationDelay: "0.1s" }}>
        {platform === "ios"
          ? <IosGuide onDismiss={onDismiss} />
          : <AndroidGuide onDismiss={onDismiss} />
        }
      </div>
    </main>
  );
}
