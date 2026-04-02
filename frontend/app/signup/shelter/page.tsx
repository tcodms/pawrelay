"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { signupShelter, ApiError } from "@/lib/api";
import { getErrorMessage } from "@/lib/errors";

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


export default function ShelterSignupPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    name: "",
    email: "",
    businessNumber: "",
    password: "",
    passwordConfirm: "",
  });
  const [showPw, setShowPw] = useState(false);
  const [showPwConfirm, setShowPwConfirm] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<{
    email?: string;
    password?: string;
    passwordConfirm?: string;
  }>({});
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const { name } = e.target;
    setForm((prev) => ({ ...prev, [name]: e.target.value }));
    if (name === "email" || name === "password" || name === "passwordConfirm") {
      setFieldErrors((prev) => ({ ...prev, [name]: undefined }));
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    const errors: typeof fieldErrors = {};
    if (!form.email.includes("@")) errors.email = "올바른 이메일 형식이 아닙니다.";
    if (form.password.length < 8) errors.password = "비밀번호는 8자 이상이어야 합니다.";
    if (form.password !== form.passwordConfirm) errors.passwordConfirm = "비밀번호가 일치하지 않습니다.";

    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      return;
    }
    setFieldErrors({});

    setLoading(true);
    try {
      await signupShelter({
        name: form.name,
        email: form.email,
        password: form.password,
        business_registration_number: form.businessNumber,
      });
      router.replace(`/signup/verify-email?email=${encodeURIComponent(form.email)}`);
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

  /* ── 가입 폼 ────────────────────────────────────────────────── */
  return (
    <main className="flex min-h-screen flex-col bg-white">
      {/* 상단 네비 */}
      <header className="sticky top-0 z-10 flex items-center gap-3 border-b border-gray-100 bg-white/90 px-4 py-4 backdrop-blur-sm">
        <Link
          href="/signup"
          className="flex h-9 w-9 items-center justify-center rounded-xl text-gray-500 transition-colors hover:bg-gray-100 active:bg-gray-200"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
        </Link>
        <h2 className="text-[17px] font-bold text-gray-900">보호소 회원가입</h2>
      </header>

      {/* 폼 */}
      <div className="flex flex-1 flex-col px-6 py-6">
        {/* 안내 배너 */}
        <div className="mb-4 flex items-start gap-2.5 rounded-xl bg-blue-50 px-4 py-3 animate-slide-up">
          <svg className="mt-0.5 shrink-0 text-blue-400" width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z" />
          </svg>
          <p className="text-[12px] leading-relaxed text-blue-600">
            가입 후 관리자 승인이 완료되어야 대시보드를 이용하실 수 있습니다.
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="flex flex-1 flex-col gap-3.5 animate-slide-up"
          style={{ animationDelay: "0.05s" }}
        >
          {/* 보호소 이름 */}
          <div className="space-y-1.5">
            <label htmlFor="name" className="block text-[13px] font-semibold text-gray-500">
              보호소 이름
            </label>
            <input
              id="name"
              name="name"
              type="text"
              required
              value={form.name}
              onChange={handleChange}
              placeholder="보호소 이름을 입력해 주세요"
              className={INPUT}
            />
          </div>

          {/* 이메일 */}
          <div className="space-y-1.5">
            <label htmlFor="email" className="block text-[13px] font-semibold text-gray-500">
              이메일
            </label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              required
              value={form.email}
              onChange={handleChange}
              placeholder="이메일 주소를 입력해 주세요"
              className={`${INPUT} ${fieldErrors.email ? "border-red-400 focus:border-red-400" : ""}`}
            />
            {fieldErrors.email && <p className="text-[12px] text-red-500">{fieldErrors.email}</p>}
          </div>

          {/* 사업자번호 */}
          <div className="space-y-1.5">
            <label htmlFor="businessNumber" className="block text-[13px] font-semibold text-gray-500">
              사업자등록번호 또는 동물보호센터 관리번호
            </label>
            <input
              id="businessNumber"
              name="businessNumber"
              type="text"
              required
              value={form.businessNumber}
              onChange={handleChange}
              placeholder="사업자등록번호 또는 관리번호를 입력해 주세요"
              className={INPUT}
            />
          </div>

          {/* 비밀번호 */}
          <div className="space-y-1.5">
            <label htmlFor="password" className="block text-[13px] font-semibold text-gray-500">
              비밀번호
            </label>
            <div className="relative">
              <input
                id="password"
                name="password"
                type={showPw ? "text" : "password"}
                autoComplete="new-password"
                required
                value={form.password}
                onChange={handleChange}
                placeholder="영문+숫자+특수문자를 포함해 주세요"
                className={`${INPUT} pr-12 ${fieldErrors.password ? "border-red-400 focus:border-red-400" : ""}`}
              />
              <button
                type="button"
                tabIndex={-1}
                aria-label={showPw ? "비밀번호 숨기기" : "비밀번호 보기"}
                onClick={() => setShowPw((v) => !v)}
                className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-400 transition-colors hover:text-gray-600"
              >
                <EyeIcon visible={showPw} />
              </button>
            </div>
            {fieldErrors.password && <p className="text-[12px] text-red-500">{fieldErrors.password}</p>}
          </div>

          {/* 비밀번호 확인 */}
          <div className="space-y-1.5">
            <label htmlFor="passwordConfirm" className="block text-[13px] font-semibold text-gray-500">
              비밀번호 확인
            </label>
            <div className="relative">
              <input
                id="passwordConfirm"
                name="passwordConfirm"
                type={showPwConfirm ? "text" : "password"}
                autoComplete="new-password"
                required
                value={form.passwordConfirm}
                onChange={handleChange}
                placeholder="비밀번호를 다시 입력해 주세요"
                className={`${INPUT} pr-12 ${fieldErrors.passwordConfirm ? "border-red-400 focus:border-red-400" : ""}`}
              />
              <button
                type="button"
                tabIndex={-1}
                aria-label={showPwConfirm ? "비밀번호 숨기기" : "비밀번호 보기"}
                onClick={() => setShowPwConfirm((v) => !v)}
                className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-400 transition-colors hover:text-gray-600"
              >
                <EyeIcon visible={showPwConfirm} />
              </button>
            </div>
            {fieldErrors.passwordConfirm && <p className="text-[12px] text-red-500">{fieldErrors.passwordConfirm}</p>}
          </div>

          {/* 에러 */}
          {error && (
            <div role="alert" className="flex items-start gap-2.5 rounded-xl bg-red-50 px-4 py-3 animate-fade-in">
              <svg className="mt-px shrink-0 text-red-400" width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
              </svg>
              <p className="text-[13px] leading-snug text-red-600">{error}</p>
            </div>
          )}

          {/* 하단 버튼 */}
          <div className="mt-auto space-y-4 pt-4">
            <button
              type="submit"
              disabled={loading}
              className="h-14 w-full rounded-2xl bg-orange-500 text-[15px] font-bold text-white shadow-md shadow-orange-100 transition-all duration-150 active:scale-[0.97] disabled:bg-gray-100 disabled:text-gray-400 disabled:shadow-none"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2.5">
                  <Spinner />
                  신청 중...
                </span>
              ) : (
                "가입 신청하기"
              )}
            </button>

            <p className="text-center text-[13px] text-gray-400">
              이미 계정이 있으신가요?{" "}
              <Link href="/login" className="font-bold text-orange-500">
                로그인
              </Link>
            </p>
          </div>
        </form>
      </div>
    </main>
  );
}
