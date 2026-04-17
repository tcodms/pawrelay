"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";

function ResultContent() {
  const searchParams = useSearchParams();
  const isSuccess = searchParams.get("success") === "true";

  if (isSuccess) {
    return (
      <main className="relative flex min-h-screen flex-col items-center justify-center bg-gray-50 overflow-hidden px-6 py-12">

        {/* 상단 물결 장식 */}
        <div className="pointer-events-none absolute inset-x-0 top-0 z-0">
          <svg viewBox="0 0 390 180" xmlns="http://www.w3.org/2000/svg" className="w-full">
            <path d="M0 0 L390 0 L390 130 C320 158 255 110 185 130 C115 150 55 165 0 145 Z" fill="#EEA968" opacity="0.55"/>
            <path d="M265 0 L390 0 L390 100 C372 124 338 108 305 80 C275 56 260 25 265 0 Z" fill="#7A4A28" opacity="0.18"/>
          </svg>
        </div>

        <div className="relative z-10 w-full max-w-sm animate-slide-up">
          <div className="rounded-3xl bg-white p-8 shadow-lg shadow-[#EEA968]/15">

            {/* 아이콘 */}
            <div className="mb-6 flex flex-col items-center gap-3 animate-scale-in">
              <div className="flex h-20 w-20 items-center justify-center rounded-[28px] bg-[#EEA968] shadow-lg shadow-[#EEA968]/30">
                <svg width="38" height="38" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              </div>
              <p className="text-[13px] font-semibold text-[#EEA968]">PawRelay</p>
            </div>

            {/* 텍스트 */}
            <div className="mb-7 text-center">
              <h1 className="text-[22px] font-bold text-gray-900">이메일 인증 완료! 🐾</h1>
              <p className="mt-2.5 text-[13px] leading-relaxed text-gray-500">
                인증이 완료되었어요.<br />
                이제 PawRelay의 모든 기능을 사용할 수 있어요.
              </p>
            </div>

            {/* 로그인 버튼 */}
            <Link
              href="/login"
              className="flex h-14 w-full items-center justify-center rounded-full bg-[#EEA968] text-[15px] font-bold text-white shadow-md shadow-[#EEA968]/20 transition-all duration-150 active:scale-[0.97] hover:bg-[#D99A55]"
            >
              로그인하러 가기
            </Link>
          </div>
        </div>
      </main>
    );
  }

  // 인증 실패 / 링크 만료
  return (
    <main className="relative flex min-h-screen flex-col items-center justify-center bg-gray-50 overflow-hidden px-6 py-12">

      {/* 상단 물결 장식 */}
      <div className="pointer-events-none absolute inset-x-0 top-0 z-0">
        <svg viewBox="0 0 390 180" xmlns="http://www.w3.org/2000/svg" className="w-full">
          <path d="M0 0 L390 0 L390 130 C320 158 255 110 185 130 C115 150 55 165 0 145 Z" fill="#EEA968" opacity="0.55"/>
          <path d="M265 0 L390 0 L390 100 C372 124 338 108 305 80 C275 56 260 25 265 0 Z" fill="#7A4A28" opacity="0.18"/>
        </svg>
      </div>

      <div className="relative z-10 w-full max-w-sm animate-slide-up">
        <div className="rounded-3xl bg-white p-8 shadow-lg shadow-[#EEA968]/15">

          {/* 아이콘 */}
          <div className="mb-6 flex flex-col items-center gap-3 animate-scale-in">
            <div className="flex h-20 w-20 items-center justify-center rounded-[28px] bg-gray-100 shadow-sm">
              <svg width="38" height="38" viewBox="0 0 24 24" fill="none" stroke="#9CA3AF" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
            </div>
            <p className="text-[13px] font-semibold text-[#EEA968]">PawRelay</p>
          </div>

          {/* 텍스트 */}
          <div className="mb-6 text-center">
            <h1 className="text-[20px] font-bold text-gray-900">인증 링크가 만료되었어요</h1>
            <p className="mt-2.5 text-[13px] leading-relaxed text-gray-500">
              링크가 유효하지 않거나 이미 만료되었습니다.<br />
              아래에서 인증 메일을 다시 받아보세요.
            </p>
          </div>

          {/* 안내 카드 */}
          <div className="mb-6 rounded-2xl bg-[#FDF3EC] px-4 py-3.5">
            <p className="text-[12px] leading-relaxed text-[#7A4A28]">
              인증 메일은 발송 후 <span className="font-bold">24시간</span> 동안만 유효합니다.
              메일이 없다면 스팸함도 확인해 주세요.
            </p>
          </div>

          {/* 버튼들 */}
          <div className="flex flex-col gap-2.5">
            <Link
              href="/signup/verify-email"
              className="flex h-14 w-full items-center justify-center rounded-full bg-[#EEA968] text-[15px] font-bold text-white shadow-md shadow-[#EEA968]/20 transition-all duration-150 active:scale-[0.97] hover:bg-[#D99A55]"
            >
              인증 메일 안내 다시 보기
            </Link>
            <Link
              href="/login"
              className="flex h-12 w-full items-center justify-center rounded-full border border-gray-200 text-[14px] font-semibold text-gray-500 transition-colors hover:bg-gray-50"
            >
              로그인 화면으로 이동
            </Link>
          </div>
        </div>
      </div>
    </main>
  );
}

export default function VerifyEmailResultPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-[#EEA968] border-t-transparent" />
      </div>
    }>
      <ResultContent />
    </Suspense>
  );
}
