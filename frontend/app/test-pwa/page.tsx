"use client";

import { useState } from "react";
import PwaInstallPrompt from "@/components/PwaInstallPrompt";

/**
 * PWA 설치 안내 모달 테스트 페이지
 * 확인 후 이 파일(app/test-pwa/)을 삭제하세요.
 */
export default function TestPwaPage() {
  if (process.env.NODE_ENV !== "development") return null;
  const [show, setShow] = useState(false);

  if (show) {
    return <PwaInstallPrompt onDismiss={() => setShow(false)} />;
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 bg-gray-50 p-8">
      <p className="text-[13px] text-gray-500">
        Chrome DevTools → 상단 기기 아이콘(Toggle device toolbar) →
        기기를 <strong>iPhone</strong> 또는 <strong>Pixel</strong>로 설정한 뒤 버튼을 누르세요.
      </p>
      <button
        onClick={() => setShow(true)}
        className="rounded-2xl bg-orange-500 px-8 py-4 text-[15px] font-bold text-white shadow-md shadow-orange-100"
      >
        PWA 설치 안내 모달 열기
      </button>
    </main>
  );
}
