/**
 * beforeinstallprompt 이벤트는 페이지 초기 로드 직후 한 번만 발생합니다.
 * React 컴포넌트가 마운트되기 전에 이미 발생할 수 있으므로
 * 모듈 레벨 변수로 저장해 두고 필요할 때 꺼내 씁니다.
 */

interface BeforeInstallPromptEvent extends Event {
  prompt(): Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

let _deferredPrompt: BeforeInstallPromptEvent | null = null;

export function initPwaPromptCapture(): void {
  if (typeof window === "undefined") return;
  window.addEventListener("beforeinstallprompt", (e) => {
    _deferredPrompt = e as BeforeInstallPromptEvent;
  });
}

export function getDeferredInstallPrompt(): BeforeInstallPromptEvent | null {
  return _deferredPrompt;
}

export function clearDeferredInstallPrompt(): void {
  _deferredPrompt = null;
}
