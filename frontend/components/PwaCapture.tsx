"use client";

// 앱 최초 로드 시점에 beforeinstallprompt 이벤트를 캡처합니다.
// 이 컴포넌트를 RootLayout에 포함시켜야 로그인 전에 이벤트를 놓치지 않습니다.
import "@/lib/pwa";

export default function PwaCapture() {
  return null;
}
