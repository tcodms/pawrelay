import Link from "next/link";

function ChevronRight() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 18l6-6-6-6" />
    </svg>
  );
}

export default function SignupPage() {
  return (
    <main className="flex min-h-screen flex-col bg-white">
      <div className="flex flex-1 flex-col items-center justify-center px-6 py-16">
        {/* 브랜드 */}
        <div className="mb-10 text-center animate-slide-up">
          <h1 className="font-[family-name:var(--font-fredoka)] text-[42px] font-bold text-orange-500 leading-none">
            PawRelay
          </h1>
          <p className="mt-2 text-[13px] font-medium text-gray-400">유기동물 릴레이 이동봉사</p>
        </div>

        {/* 역할 선택 */}
        <div
          className="w-full max-w-sm animate-slide-up"
          style={{ animationDelay: "0.07s" }}
        >
          <p className="mb-5 text-center text-[15px] font-bold text-gray-800">
            어떤 역할로 가입하시겠어요?
          </p>

          <div className="space-y-3">
            {/* 봉사자 카드 */}
            <Link
              href="/signup/volunteer"
              className="group flex w-full items-center gap-4 rounded-2xl border-2 border-gray-100 bg-white p-5 transition-all duration-150 active:scale-[0.98] hover:border-orange-200 hover:bg-orange-50"
            >
              <div className="flex h-[52px] w-[52px] shrink-0 items-center justify-center rounded-xl bg-orange-100">
                <span className="text-[26px] leading-none">🐾</span>
              </div>
              <div className="flex-1 text-left">
                <p className="text-[15px] font-bold text-gray-900 transition-colors group-hover:text-orange-600">
                  봉사자
                </p>
                <p className="mt-0.5 text-[12px] leading-relaxed text-gray-400">
                  동물 이동봉사에 참여하고 싶어요
                </p>
              </div>
              <span className="shrink-0 text-gray-300 transition-colors group-hover:text-orange-400">
                <ChevronRight />
              </span>
            </Link>

            {/* 보호소 카드 */}
            <Link
              href="/signup/shelter"
              className="group flex w-full items-center gap-4 rounded-2xl border-2 border-gray-100 bg-white p-5 transition-all duration-150 active:scale-[0.98] hover:border-orange-200 hover:bg-orange-50"
            >
              <div className="flex h-[52px] w-[52px] shrink-0 items-center justify-center rounded-xl bg-blue-50">
                <span className="text-[26px] leading-none">🏠</span>
              </div>
              <div className="flex-1 text-left">
                <p className="text-[15px] font-bold text-gray-900 transition-colors group-hover:text-orange-600">
                  보호소
                </p>
                <p className="mt-0.5 text-[12px] leading-relaxed text-gray-400">
                  보호 중인 동물의 이동을 요청할게요
                </p>
              </div>
              <span className="shrink-0 text-gray-300 transition-colors group-hover:text-orange-400">
                <ChevronRight />
              </span>
            </Link>
          </div>

          <p className="mt-8 text-center text-[13px] text-gray-400">
            이미 계정이 있으신가요?{" "}
            <Link href="/login" className="font-bold text-orange-500">
              로그인
            </Link>
          </p>
        </div>
      </div>
    </main>
  );
}
