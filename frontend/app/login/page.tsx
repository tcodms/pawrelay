"use client";

import { useState, useEffect, useRef, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { login, ApiError } from "@/lib/api";
import { getErrorMessage } from "@/lib/errors";
import EyeIcon from "@/components/ui/EyeIcon";
import Spinner from "@/components/ui/Spinner";
import PwaInstallModal from "@/components/PwaInstallModal";

const INPUT_BASE =
  "h-12 w-full rounded-2xl border bg-white px-4 text-base text-gray-700 placeholder:text-gray-400 shadow-sm transition-colors duration-150 focus:outline-none";
const INPUT_NORMAL = `${INPUT_BASE} border-gray-200 focus:border-[#EEA968]/60`;
const INPUT_ERROR  = `${INPUT_BASE} border-red-300 bg-red-50 focus:border-red-400`;

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

type FieldErrors = { email: string; password: string };

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw]     = useState(false);

  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({ email: "", password: "" });
  const [globalError, setGlobalError] = useState("");
  const [emailNotVerified, setEmailNotVerified] = useState(false);
  const [toast, setToast]   = useState("");
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const pendingRole = useRef<string | null>(null);
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (searchParams.get("verified") === "true") {
      setToast("이메일 인증이 완료되었습니다 ✓");
      toastTimer.current = setTimeout(() => setToast(""), 3500);
    }
    if (searchParams.get("error") === "INVALID_TOKEN") {
      setGlobalError("유효하지 않은 인증 링크입니다. 다시 시도해 주세요.");
    }
    return () => { if (toastTimer.current) clearTimeout(toastTimer.current); };
  }, [searchParams]);

  function handleEmailChange(e: React.ChangeEvent<HTMLInputElement>) {
    setEmail(e.target.value);
    if (fieldErrors.email) setFieldErrors((prev) => ({ ...prev, email: "" }));
    if (globalError) setGlobalError("");
    if (emailNotVerified) setEmailNotVerified(false);
  }

  function handlePasswordChange(e: React.ChangeEvent<HTMLInputElement>) {
    setPassword(e.target.value);
    if (fieldErrors.password) setFieldErrors((prev) => ({ ...prev, password: "" }));
    if (globalError) setGlobalError("");
  }

  function validate(): boolean {
    const errors: FieldErrors = { email: "", password: "" };
    if (!email.trim()) errors.email = "이메일을 입력해 주세요.";
    else if (!EMAIL_REGEX.test(email)) errors.email = "올바른 이메일 형식이 아닙니다.";
    if (!password) errors.password = "비밀번호를 입력해 주세요.";
    setFieldErrors(errors);
    return !errors.email && !errors.password;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setGlobalError("");
    if (!validate()) return;
    setLoading(true);
    try {
      const { user } = await login(email, password);
      pendingRole.current = user.role;
      const hasPwaFlag = localStorage.getItem("pwa_welcome_pending") === "1";
      const isMobile = /iPad|iPhone|iPod|Android/i.test(navigator.userAgent);
      if (hasPwaFlag && isMobile) {
        setShowModal(true);
      } else {
        localStorage.removeItem("pwa_welcome_pending");
        router.replace(user.role === "volunteer" ? "/volunteer/posts" : "/dashboard");
      }
    } catch (err) {
      if (err instanceof ApiError && err.code === "INVALID_CREDENTIALS") {
        setGlobalError("이메일 또는 비밀번호를 다시 확인해 주세요.");
      } else if (err instanceof ApiError && err.code === "EMAIL_NOT_VERIFIED") {
        setEmailNotVerified(true);
      } else {
        setGlobalError(
          err instanceof ApiError
            ? getErrorMessage(err.code)
            : getErrorMessage("UNKNOWN_ERROR"),
        );
      }
    } finally {
      setLoading(false);
    }
  }

  function handleModalDismiss() {
    localStorage.removeItem("pwa_welcome_pending");
    router.replace(pendingRole.current === "volunteer" ? "/volunteer/posts" : "/dashboard");
  }

  if (showModal) {
    return <PwaInstallModal onDismiss={handleModalDismiss} />;
  }

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

      {/* 토스트 */}
      {toast && (
        <div className="fixed inset-x-0 top-5 z-50 flex justify-center px-6 animate-fade-in">
          <div className="flex items-center gap-2.5 rounded-2xl bg-gray-900 px-5 py-3.5 shadow-xl">
            <svg className="shrink-0 text-green-400" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <polyline points="20 6 9 17 4 12" />
            </svg>
            <span className="text-[13px] font-semibold text-white">{toast}</span>
          </div>
        </div>
      )}

      <div className="relative z-10 flex flex-1 flex-col items-center justify-center px-6 py-16">

        {/* 통합 카드: 브랜드 + 폼 */}
        <div
          className="w-full max-w-sm rounded-3xl bg-white p-8 shadow-lg shadow-[#EEA968]/15 animate-slide-up"
          style={{ animationDelay: "0.07s" }}
        >
          {/* 브랜드 */}
          <div className="mb-8 text-center">
            <h1 className="font-[family-name:var(--font-fredoka)] text-[34px] font-bold text-[#EEA968] leading-none">
              PawRelay
            </h1>
            <p className="mt-2 text-[11px] font-medium text-[#B8A090]">유기동물 릴레이 이동봉사</p>
          </div>

          <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">

            {/* 이메일 */}
            <div className="space-y-1.5">
              <label htmlFor="email" className="block text-[13px] font-semibold text-gray-500">이메일</label>
              <input
                id="email" type="email" inputMode="email" autoComplete="email"
                value={email} onChange={handleEmailChange}
                placeholder="이메일 주소를 입력하세요"
                className={fieldErrors.email ? INPUT_ERROR : INPUT_NORMAL}
              />
              {fieldErrors.email && (
                <p role="alert" className="text-[12px] text-red-500 animate-fade-in">{fieldErrors.email}</p>
              )}
            </div>

            {/* 비밀번호 */}
            <div className="space-y-1.5">
              <label htmlFor="password" className="block text-[13px] font-semibold text-gray-500">비밀번호</label>
              <div className="relative">
                <input
                  id="password" type={showPw ? "text" : "password"} autoComplete="current-password"
                  value={password} onChange={handlePasswordChange}
                  placeholder="비밀번호를 입력하세요"
                  className={`${fieldErrors.password ? INPUT_ERROR : INPUT_NORMAL} pr-12`}
                />
                <button type="button" tabIndex={-1}
                  aria-label={showPw ? "비밀번호 숨기기" : "비밀번호 보기"}
                  onClick={() => setShowPw((v) => !v)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                  <EyeIcon visible={showPw} />
                </button>
              </div>
              {fieldErrors.password && (
                <p role="alert" className="text-[12px] text-red-500 animate-fade-in">{fieldErrors.password}</p>
              )}
            </div>

            {/* 이메일 미인증 안내 */}
            {emailNotVerified && (
              <div role="alert" className="rounded-2xl bg-[#FDF3EC] border border-[#EEA968]/20 px-4 py-3.5 animate-fade-in">
                <p className="text-[13px] font-semibold text-[#7A4A28] mb-1">이메일 인증이 필요합니다</p>
                <p className="text-[12px] text-[#EEA968] leading-relaxed mb-2.5">
                  가입 시 발송된 인증 메일의 버튼을 클릭한 후 다시 로그인해 주세요.
                </p>
                <Link
                  href={`/signup/verify-email?email=${encodeURIComponent(email)}`}
                  className="inline-block text-[12px] font-semibold text-[#EEA968] underline underline-offset-2"
                >
                  인증 메일 안내 다시 보기
                </Link>
              </div>
            )}

            {/* 전역 에러 */}
            {globalError && (
              <div role="alert" className="flex items-start gap-2 animate-fade-in">
                <svg className="mt-0.5 shrink-0 text-red-400" width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
                </svg>
                <p className="text-sm text-red-500 leading-snug">{globalError}</p>
              </div>
            )}

            {/* 로그인 버튼 */}
            <button
              type="submit" disabled={loading}
              className="mt-2 h-14 w-full rounded-full bg-[#EEA968] text-[15px] font-bold text-white shadow-md shadow-[#EEA968]/20 transition-all duration-150 active:scale-[0.97] hover:bg-[#D99A55] disabled:bg-gray-100 disabled:text-gray-400 disabled:shadow-none"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2.5">
                  <Spinner />
                  로그인 중...
                </span>
              ) : "로그인"}
            </button>
          </form>

          <p className="mt-5 text-center text-[13px] text-gray-400">
            계정이 없으신가요?{" "}
            <Link href="/signup" className="font-bold text-[#EEA968]">회원가입</Link>
          </p>
        </div>
      </div>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}
