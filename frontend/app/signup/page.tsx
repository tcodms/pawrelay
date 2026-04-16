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
    <main className="relative flex min-h-screen flex-col bg-gray-50 overflow-hidden">

      {/* 상단 물결 장식 */}
      {/* 모바일: 세로 2배 viewBox → 화면 1/3 높이 */}
      <div className="pointer-events-none absolute inset-x-0 top-0 z-0 md:hidden">
        <svg viewBox="0 0 390 280" xmlns="http://www.w3.org/2000/svg" className="w-full">
          <path d="M0 0 L390 0 L390 190 C320 236 255 160 185 190 C115 220 55 244 0 210 Z" fill="#EEA968" opacity="0.55"/>
          <path d="M265 0 L390 0 L390 150 C372 184 338 160 305 120 C275 88 260 40 265 0 Z" fill="#7A4A28" opacity="0.22"/>
        </svg>
      </div>
      {/* 데스크탑: 원래 비율 그대로 (로고가 카드 안에 있어 겹칠 일 없음) */}
      <div className="pointer-events-none absolute inset-x-0 top-0 z-0 hidden md:block">
        <svg viewBox="0 0 390 140" xmlns="http://www.w3.org/2000/svg" className="w-full">
          <path d="M0 0 L390 0 L390 95 C320 118 255 80 185 95 C115 110 55 122 0 105 Z" fill="#EEA968" opacity="0.55"/>
          <path d="M265 0 L390 0 L390 75 C372 92 338 80 305 60 C275 44 260 20 265 0 Z" fill="#7A4A28" opacity="0.22"/>
        </svg>
      </div>

      <div className="relative z-10 flex flex-1 flex-col items-center justify-center px-6 py-16">

        {/* 통합 카드: 브랜드 + 역할 선택 */}
        <div className="w-full max-w-sm rounded-3xl bg-white p-8 shadow-lg shadow-[#EEA968]/15 animate-slide-up">

          {/* 브랜드 */}
          <div className="mb-8 text-center">
            <h1 className="font-[family-name:var(--font-fredoka)] text-[34px] font-bold text-[#EEA968] leading-none">
              PawRelay
            </h1>
            <p className="mt-2 text-[11px] font-medium text-[#B8A090]">유기동물 릴레이 이동봉사</p>
          </div>

          {/* 역할 선택 */}
          <p className="mb-5 text-center text-[15px] font-bold text-gray-700">
            어떤 역할로 가입하시겠어요?
          </p>

          <div className="space-y-3">
            {/* 봉사자 카드 */}
            <Link
              href="/signup/volunteer"
              className="group flex w-full items-center gap-4 rounded-2xl bg-[#FAFAFA] border border-gray-100 p-5 transition-all duration-150 active:scale-[0.98] hover:border-[#EEA968]/30 hover:shadow-md hover:shadow-[#EEA968]/15"
            >
              <div className="flex h-[52px] w-[52px] shrink-0 items-center justify-center rounded-2xl bg-[#FDF3EC]">
                <span className="text-[26px] leading-none">🐾</span>
              </div>
              <div className="flex-1 text-left">
                <p className="text-[15px] font-bold text-gray-700 transition-colors group-hover:text-[#EEA968]">
                  봉사자
                </p>
                <p className="mt-0.5 text-[12px] leading-relaxed text-gray-400">
                  동물 이동봉사에 참여하고 싶어요
                </p>
              </div>
              <span className="shrink-0 text-gray-300 transition-colors group-hover:text-[#EEA968]">
                <ChevronRight />
              </span>
            </Link>

            {/* 보호소 카드 */}
            <Link
              href="/signup/shelter"
              className="group flex w-full items-center gap-4 rounded-2xl bg-[#FAFAFA] border border-gray-100 p-5 transition-all duration-150 active:scale-[0.98] hover:border-[#EEA968]/30 hover:shadow-md hover:shadow-[#EEA968]/15"
            >
              <div className="flex h-[52px] w-[52px] shrink-0 items-center justify-center rounded-2xl bg-[#FDF3EC]">
                <span className="text-[26px] leading-none">🏠</span>
              </div>
              <div className="flex-1 text-left">
                <p className="text-[15px] font-bold text-gray-700 transition-colors group-hover:text-[#EEA968]">
                  보호소
                </p>
                <p className="mt-0.5 text-[11px] leading-relaxed text-gray-400">
                  보호 중인 동물의<br />이동을 요청할게요
                </p>
              </div>
              <span className="shrink-0 text-gray-300 transition-colors group-hover:text-[#EEA968]">
                <ChevronRight />
              </span>
            </Link>
          </div>

          <p className="mt-8 text-center text-[13px] text-gray-400">
            이미 계정이 있으신가요?{" "}
            <Link href="/login" className="font-bold text-[#EEA968]">로그인</Link>
          </p>
        </div>
      </div>
    </main>
  );
}
