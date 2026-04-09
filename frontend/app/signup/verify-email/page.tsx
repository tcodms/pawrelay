"use client";

import { Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";

function VerifyEmailContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const email = searchParams.get("email") ?? "";

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-white px-6 py-12">
      {/* 아이콘 */}
      <div className="mb-8 flex flex-col items-center gap-3 animate-scale-in">
        <div className="flex h-20 w-20 items-center justify-center rounded-[28px] bg-orange-500 shadow-lg shadow-orange-200">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
            <polyline points="22,6 12,13 2,6" />
          </svg>
        </div>
        <p className="text-[13px] font-semibold text-orange-500">PawRelay</p>
      </div>

      <div className="w-full max-w-sm animate-slide-up" style={{ animationDelay: "0.1s" }}>
        {/* 안내 텍스트 */}
        <div className="mb-6 text-center">
          <h2 className="text-[20px] font-bold text-gray-900">이메일을 확인해 주세요</h2>
          <p className="mt-2 text-[13px] leading-relaxed text-gray-500">
            아래 주소로 인증 메일을 발송했습니다.
          </p>
          {email && (
            <p className="mt-2 text-[14px] font-semibold text-orange-500 break-all">
              {email}
            </p>
          )}
        </div>

        {/* 안내 카드 */}
        <div className="mb-6 flex flex-col gap-2.5">
          <div className="flex items-start gap-3 rounded-2xl bg-orange-50 px-4 py-3.5">
            <span className="mt-0.5 text-[18px] leading-none shrink-0">1</span>
            <p className="text-[13px] leading-snug text-gray-700">
              받은 메일함에서 <span className="font-semibold">PawRelay</span> 발신 메일을 열어주세요.
            </p>
          </div>
          <div className="flex items-start gap-3 rounded-2xl bg-orange-50 px-4 py-3.5">
            <span className="mt-0.5 text-[18px] leading-none shrink-0">2</span>
            <p className="text-[13px] leading-snug text-gray-700">
              메일 안의 <span className="font-semibold">"이메일 인증하기"</span> 버튼을 탭하세요.
            </p>
          </div>
          <div className="flex items-start gap-3 rounded-2xl bg-orange-50 px-4 py-3.5">
            <span className="mt-0.5 text-[18px] leading-none shrink-0">3</span>
            <p className="text-[13px] leading-snug text-gray-700">
              인증 완료 후 로그인 화면으로 이동합니다.
            </p>
          </div>
        </div>

        {/* 스팸 안내 + 재발송 */}
        <div className="mb-6 flex flex-col gap-2">
          <div className="flex items-start gap-2 rounded-xl bg-gray-50 px-4 py-3">
            <svg className="mt-0.5 shrink-0 text-gray-400" width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z" />
            </svg>
            <p className="text-[12px] leading-relaxed text-gray-400">
              메일이 오지 않으면 스팸함을 확인하거나 아래 버튼으로 재발송하세요.
            </p>
          </div>

          {/* TODO: 백엔드 POST /auth/resend-verification 구현 후 연동 */}
          <button
            type="button"
            disabled
            className="w-full rounded-xl border border-gray-200 py-3 text-[13px] font-semibold text-gray-300"
          >
            인증 메일 재발송
          </button>
        </div>

        {/* 로그인 페이지로 */}
        <Link
          href="/login"
          className="flex h-14 w-full items-center justify-center rounded-2xl bg-orange-500 text-[15px] font-bold text-white shadow-md shadow-orange-100 transition-all duration-150 active:scale-[0.97]"
        >
          로그인 화면으로 이동
        </Link>

        <button
          type="button"
          onClick={() => router.replace("/signup")}
          className="mt-3 w-full rounded-2xl border border-gray-200 py-3.5 text-[14px] font-semibold text-gray-500 transition-colors active:bg-gray-50"
        >
          다른 계정으로 가입하기
        </button>
      </div>
    </main>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense>
      <VerifyEmailContent />
    </Suspense>
  );
}
