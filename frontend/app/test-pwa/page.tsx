"use client";

import { useState } from "react";
import PwaInstallModal from "@/components/PwaInstallModal";
import PwaInstallToast from "@/components/PwaInstallToast";

/** PWA 설치 안내 UI 개발용 테스트 페이지 (프로덕션 노출 없음) */
export default function TestPwaPage() {
  const [show, setShow] = useState<"modal" | "toast" | null>(null);

  if (process.env.NODE_ENV !== "development") return null;

  if (show === "modal") {
    return <PwaInstallModal onDismiss={() => setShow(null)} />;
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 bg-gray-50 p-8">
      {show === "toast" && <PwaInstallToast />}

      <p className="text-[13px] text-gray-500 text-center max-w-xs">
        Chrome DevTools → 상단 기기 아이콘(Toggle device toolbar) →
        기기를 <strong>iPhone</strong> 또는 <strong>Pixel</strong>로 설정한 뒤 버튼을 누르세요.
      </p>

      <div className="flex flex-col gap-3 w-full max-w-xs">
        <button
          onClick={() => setShow("modal")}
          className="rounded-2xl bg-orange-500 px-8 py-4 text-[15px] font-bold text-white shadow-md shadow-orange-100 active:scale-[0.97] transition-transform"
        >
          PwaInstallModal (회원가입 후)
        </button>
        <button
          onClick={() => {
            localStorage.removeItem("pwa_toast_dismissed");
            setShow("toast");
          }}
          className="rounded-2xl bg-orange-100 px-8 py-4 text-[15px] font-bold text-orange-600 active:scale-[0.97] transition-transform"
        >
          PwaInstallToast (로그인 후)
        </button>
        {show === "toast" && (
          <button
            onClick={() => setShow(null)}
            className="rounded-2xl border border-gray-200 px-8 py-3 text-[14px] font-semibold text-gray-500"
          >
            토스트 닫기
          </button>
        )}
      </div>
    </main>
  );
}
