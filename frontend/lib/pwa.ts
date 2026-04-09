/**
 * beforeinstallprompt 이벤트는 페이지 초기 로드 직후 한 번만 발생합니다.
 * 컴포넌트 마운트 전에 이미 발생할 수 있으므로 모듈 로드 시점에 즉시 등록합니다.
 */

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
