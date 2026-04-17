"use client";

import { useEffect } from "react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    if (process.env.NODE_ENV !== "production") {
      console.error(error);
    }
  }, [error]);

  return (
    <main className="min-h-screen bg-gray-50 flex flex-col items-center justify-center gap-4 px-6">
      <p className="text-[48px] leading-none">😢</p>
      <p className="text-[20px] font-bold text-gray-800">문제가 발생했어요</p>
      <p className="text-[13px] text-gray-400 text-center">
        일시적인 오류입니다. 잠시 후 다시 시도해 주세요.
      </p>
      <button
        onClick={reset}
        className="mt-2 rounded-full bg-[#EEA968] px-6 py-2.5 text-[14px] font-bold text-white shadow-md shadow-[#EEA968]/20"
      >
        다시 시도
      </button>
    </main>
  );
}
