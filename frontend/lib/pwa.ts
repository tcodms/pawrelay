/**
 * beforeinstallprompt 이벤트는 페이지 초기 로드 직후 한 번만 발생합니다.
 * React 컴포넌트가 마운트되기 전에 이미 발생할 수 있으므로
 * 모듈 레벨 변수로 저장해 두고 필요할 때 꺼내 씁니다.
 */
let _deferredPrompt: any = null;

export function initPwaPromptCapture(): void {
  if (typeof window === "undefined") return;
  window.addEventListener("beforeinstallprompt", (e) => {
    _deferredPrompt = e;
  });
}

export function getDeferredInstallPrompt(): any {
  return _deferredPrompt;
}

export function clearDeferredInstallPrompt(): void {
  _deferredPrompt = null;
}
