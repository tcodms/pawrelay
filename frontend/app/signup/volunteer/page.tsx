"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { signupVolunteer, ApiError, AnimalSize } from "@/lib/api";
import { getErrorMessage } from "@/lib/errors";
import PwaInstallPrompt from "@/components/PwaInstallPrompt";

// ── 공용 UI 컴포넌트 ──────────────────────────────────────────────────────────

function EyeIcon({ visible }: { visible: boolean }) {
  return visible ? (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
      <line x1="1" y1="1" x2="23" y2="23" />
    </svg>
  ) : (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

function Spinner() {
  return (
    <svg className="animate-spin" width="18" height="18" viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="white" strokeWidth="3" />
      <path className="opacity-75" fill="white" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  );
}

const INPUT =
  "h-12 w-full rounded-xl border border-gray-200 bg-gray-50 px-4 text-base text-gray-900 placeholder:text-gray-400 transition-colors duration-150 focus:border-orange-400 focus:bg-white focus:outline-none";

// ── 단계 표시기 ───────────────────────────────────────────────────────────────

function StepIndicator({ current }: { current: 1 | 2 }) {
  return (
    <div className="flex items-center justify-center gap-2 py-4">
      {[1, 2].map((s) => (
        <div key={s} className="flex items-center gap-2">
          <div
            className={`flex h-7 w-7 items-center justify-center rounded-full text-[12px] font-bold transition-colors duration-200 ${
              s <= current
                ? "bg-orange-500 text-white"
                : "bg-gray-100 text-gray-400"
            }`}
          >
            {s}
          </div>
          {s === 1 && (
            <div className={`h-px w-10 transition-colors duration-200 ${current === 2 ? "bg-orange-400" : "bg-gray-200"}`} />
          )}
        </div>
      ))}
      <div className="sr-only">{current}단계 / 2단계</div>
    </div>
  );
}

// ── 에러 박스 ─────────────────────────────────────────────────────────────────

function ErrorBox({ message }: { message: string }) {
  return (
    <div role="alert" className="flex items-start gap-2.5 rounded-xl bg-red-50 px-4 py-3 animate-fade-in">
      <svg className="mt-px shrink-0 text-red-400" width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
      </svg>
      <p className="text-[13px] leading-snug text-red-600">{message}</p>
    </div>
  );
}

// ── 메인 컴포넌트 ─────────────────────────────────────────────────────────────

export default function VolunteerSignupPage() {
  const router = useRouter();
  const [step, setStep] = useState<1 | 2>(1);

  // 1단계 필드
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [showPwConfirm, setShowPwConfirm] = useState(false);

  // 2단계 필드
  const [regionInput, setRegionInput] = useState("");
  const [activityRegions, setActivityRegions] = useState<string[]>([]);
  const [vehicleAvailable, setVehicleAvailable] = useState<boolean | null>(null);
  const [maxAnimalSize, setMaxAnimalSize] = useState<AnimalSize | null>(null);

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPwaPrompt, setShowPwaPrompt] = useState(false);

  // ── 지역 칩 추가 / 제거 ─────────────────────────────────────────────────────

  function addRegion() {
    const trimmed = regionInput.trim();
    if (!trimmed || activityRegions.includes(trimmed)) {
      setRegionInput("");
      return;
    }
    setActivityRegions((prev) => [...prev, trimmed]);
    setRegionInput("");
  }

  function removeRegion(region: string) {
    setActivityRegions((prev) => prev.filter((r) => r !== region));
  }

  // ── 1단계 → 2단계 ──────────────────────────────────────────────────────────

  function handleStep1Next(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (password !== passwordConfirm) {
      setError("비밀번호가 일치하지 않습니다.");
      return;
    }
    setStep(2);
    window.scrollTo({ top: 0 });
  }

  // ── 2단계 제출 → API ────────────────────────────────────────────────────────

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (activityRegions.length === 0) {
      setError("활동 지역을 최소 1개 이상 추가해 주세요.");
      return;
    }
    if (vehicleAvailable === null) {
      setError("차량 유무를 선택해 주세요.");
      return;
    }
    if (!maxAnimalSize) {
      setError("이송 가능한 동물 크기를 선택해 주세요.");
      return;
    }

    setLoading(true);
    try {
      await signupVolunteer({
        name,
        email,
        password,
        vehicle_available: vehicleAvailable,
        max_animal_size: maxAnimalSize,
        activity_regions: activityRegions,
      });
      setShowPwaPrompt(true);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? getErrorMessage(err.code)
          : getErrorMessage("UNKNOWN_ERROR"),
      );
    } finally {
      setLoading(false);
    }
  }

  // ── 가입 완료 후 PWA 안내 화면 ─────────────────────────────────────────────

  if (showPwaPrompt) {
    return (
      <PwaInstallPrompt onDismiss={() => router.replace("/volunteer/chat")} />
    );
  }

  // ── 공통 헤더 ───────────────────────────────────────────────────────────────

  const header = (
    <header className="sticky top-0 z-10 flex items-center gap-3 border-b border-gray-100 bg-white/90 px-4 py-4 backdrop-blur-sm">
      <button
        type="button"
        onClick={() => {
          setError("");
          if (step === 2) setStep(1);
          else router.back();
        }}
        className="flex h-9 w-9 items-center justify-center rounded-xl text-gray-500 transition-colors hover:bg-gray-100 active:bg-gray-200"
        aria-label="뒤로가기"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M19 12H5M12 19l-7-7 7-7" />
        </svg>
      </button>
      <h2 className="text-[17px] font-bold text-gray-900">봉사자 회원가입</h2>
    </header>
  );

  // ── 1단계: 기본 정보 ────────────────────────────────────────────────────────

  if (step === 1) {
    return (
      <main className="flex min-h-screen flex-col bg-white">
        {header}
        <StepIndicator current={1} />

        <div className="flex flex-1 flex-col px-6 pb-8">
          <p className="mb-5 text-[13px] text-gray-400">기본 정보를 입력해 주세요.</p>

          <form onSubmit={handleStep1Next} className="flex flex-1 flex-col gap-3.5 animate-slide-up">
            {/* 이름 */}
            <div className="space-y-1.5">
              <label htmlFor="name" className="block text-[13px] font-semibold text-gray-500">이름</label>
              <input
                id="name" name="name" type="text" autoComplete="name" required
                value={name} onChange={(e) => setName(e.target.value)}
                placeholder="실명을 입력해 주세요"
                className={INPUT}
              />
            </div>

            {/* 이메일 */}
            <div className="space-y-1.5">
              <label htmlFor="email" className="block text-[13px] font-semibold text-gray-500">이메일</label>
              <input
                id="email" name="email" type="email" autoComplete="email" required
                value={email} onChange={(e) => setEmail(e.target.value)}
                placeholder="이메일 주소를 입력해 주세요"
                className={INPUT}
              />
            </div>

            {/* 비밀번호 */}
            <div className="space-y-1.5">
              <label htmlFor="password" className="block text-[13px] font-semibold text-gray-500">비밀번호</label>
              <div className="relative">
                <input
                  id="password" name="password"
                  type={showPw ? "text" : "password"}
                  autoComplete="new-password" required
                  value={password} onChange={(e) => setPassword(e.target.value)}
                  placeholder="영문+숫자+특수문자를 포함해 주세요"
                  className={`${INPUT} pr-12`}
                />
                <button type="button" tabIndex={-1} onClick={() => setShowPw((v) => !v)}
                  aria-label={showPw ? "비밀번호 숨기기" : "비밀번호 보기"}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                  <EyeIcon visible={showPw} />
                </button>
              </div>
            </div>

            {/* 비밀번호 확인 */}
            <div className="space-y-1.5">
              <label htmlFor="passwordConfirm" className="block text-[13px] font-semibold text-gray-500">비밀번호 확인</label>
              <div className="relative">
                <input
                  id="passwordConfirm" name="passwordConfirm"
                  type={showPwConfirm ? "text" : "password"}
                  autoComplete="new-password" required
                  value={passwordConfirm} onChange={(e) => setPasswordConfirm(e.target.value)}
                  placeholder="비밀번호를 다시 입력해 주세요"
                  className={`${INPUT} pr-12`}
                />
                <button type="button" tabIndex={-1} onClick={() => setShowPwConfirm((v) => !v)}
                  aria-label={showPwConfirm ? "비밀번호 숨기기" : "비밀번호 보기"}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                  <EyeIcon visible={showPwConfirm} />
                </button>
              </div>
            </div>

            {error && <ErrorBox message={error} />}

            <div className="mt-auto space-y-4 pt-4">
              <button type="submit"
                className="h-14 w-full rounded-2xl bg-orange-500 text-[15px] font-bold text-white shadow-md shadow-orange-100 transition-all duration-150 active:scale-[0.97]">
                다음
              </button>
              <p className="text-center text-[13px] text-gray-400">
                이미 계정이 있으신가요?{" "}
                <Link href="/login" className="font-bold text-orange-500">로그인</Link>
              </p>
            </div>
          </form>
        </div>
      </main>
    );
  }

  // ── 2단계: 봉사 프로필 ──────────────────────────────────────────────────────

  const ANIMAL_SIZES: { value: AnimalSize; label: string; sub: string }[] = [
    { value: "small",  label: "소형", sub: "5kg 이하" },
    { value: "medium", label: "중형", sub: "15kg 이하" },
    { value: "large",  label: "대형", sub: "15kg 초과" },
  ];

  return (
    <main className="flex min-h-screen flex-col bg-white">
      {header}
      <StepIndicator current={2} />

      <div className="flex flex-1 flex-col px-6 pb-8">
        <p className="mb-5 text-[13px] text-gray-400">봉사 활동 정보를 입력해 주세요.</p>

        <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-6 animate-slide-up">

          {/* 활동 지역 */}
          <div className="space-y-2">
            <label className="block text-[13px] font-semibold text-gray-500">
              활동 지역 <span className="font-normal text-gray-400">(복수 선택 가능)</span>
            </label>

            {/* 칩 목록 */}
            {activityRegions.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {activityRegions.map((region) => (
                  <span key={region}
                    className="inline-flex items-center gap-1.5 rounded-full bg-orange-50 px-3 py-1.5 text-[13px] font-medium text-orange-600">
                    {region}
                    <button type="button" onClick={() => removeRegion(region)}
                      aria-label={`${region} 제거`}
                      className="flex h-4 w-4 items-center justify-center rounded-full bg-orange-200 text-orange-700 transition-colors hover:bg-orange-300">
                      <svg width="8" height="8" viewBox="0 0 12 12" fill="currentColor">
                        <path d="M9.9 2.1L6 6m0 0L2.1 9.9M6 6l3.9 3.9M6 6L2.1 2.1" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
                      </svg>
                    </button>
                  </span>
                ))}
              </div>
            )}

            {/* 입력 */}
            <div className="flex gap-2">
              <input
                type="text" value={regionInput}
                onChange={(e) => setRegionInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addRegion(); } }}
                placeholder="예: 경기도, 서울 강남구"
                className={`${INPUT} flex-1`}
              />
              <button type="button" onClick={addRegion}
                className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-orange-500 text-white transition-colors active:bg-orange-600">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                  <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
                </svg>
              </button>
            </div>
          </div>

          {/* 차량 유무 */}
          <div className="space-y-2">
            <label className="block text-[13px] font-semibold text-gray-500">차량 유무</label>
            <div className="grid grid-cols-2 gap-3">
              {[{ value: true, label: "있음", icon: "🚗" }, { value: false, label: "없음", icon: "🚶" }].map((opt) => (
                <button key={String(opt.value)} type="button"
                  onClick={() => setVehicleAvailable(opt.value)}
                  className={`flex h-14 items-center justify-center gap-2 rounded-xl border-2 text-[15px] font-bold transition-all duration-150 ${
                    vehicleAvailable === opt.value
                      ? "border-orange-500 bg-orange-50 text-orange-600"
                      : "border-gray-200 bg-gray-50 text-gray-500"
                  }`}>
                  <span>{opt.icon}</span>
                  <span>{opt.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* 최대 동물 크기 */}
          <div className="space-y-2">
            <label className="block text-[13px] font-semibold text-gray-500">이송 가능한 최대 동물 크기</label>
            <div className="grid grid-cols-3 gap-2.5">
              {ANIMAL_SIZES.map((size) => (
                <button key={size.value} type="button"
                  onClick={() => setMaxAnimalSize(size.value)}
                  className={`flex flex-col items-center justify-center gap-1 rounded-xl border-2 py-4 transition-all duration-150 ${
                    maxAnimalSize === size.value
                      ? "border-orange-500 bg-orange-50"
                      : "border-gray-200 bg-gray-50"
                  }`}>
                  <span className={`text-[15px] font-bold ${maxAnimalSize === size.value ? "text-orange-600" : "text-gray-700"}`}>
                    {size.label}
                  </span>
                  <span className="text-[11px] text-gray-400">{size.sub}</span>
                </button>
              ))}
            </div>
            <p className="text-[11px] text-gray-400 pl-1">선택한 크기 이하의 동물을 모두 이송할 수 있어요.</p>
          </div>

          {error && <ErrorBox message={error} />}

          <div className="mt-auto pt-2">
            <button type="submit" disabled={loading}
              className="h-14 w-full rounded-2xl bg-orange-500 text-[15px] font-bold text-white shadow-md shadow-orange-100 transition-all duration-150 active:scale-[0.97] disabled:bg-gray-100 disabled:text-gray-400 disabled:shadow-none">
              {loading ? (
                <span className="flex items-center justify-center gap-2.5">
                  <Spinner />
                  가입 중...
                </span>
              ) : (
                "봉사자로 가입하기"
              )}
            </button>
          </div>
        </form>
      </div>
    </main>
  );
}
