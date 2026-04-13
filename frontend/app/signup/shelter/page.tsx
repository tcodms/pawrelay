"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { signupShelter, ApiError } from "@/lib/api";
import { getErrorMessage } from "@/lib/errors";
import EyeIcon from "@/components/ui/EyeIcon";
import Spinner from "@/components/ui/Spinner";
import ErrorBox from "@/components/ui/ErrorBox";
import StepIndicator from "@/components/ui/StepIndicator";

const INPUT =
  "h-12 w-full rounded-xl border border-gray-200 bg-gray-50 px-4 text-base text-gray-900 placeholder:text-gray-400 transition-colors duration-150 focus:border-orange-400 focus:bg-white focus:outline-none";

const PW_REGEX = /^(?=.*[a-zA-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]).{8,}$/;

export default function ShelterSignupPage() {
  const router = useRouter();
  const [step, setStep] = useState<1 | 2>(1);

  // 1단계
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [showPwConfirm, setShowPwConfirm] = useState(false);

  // 2단계
  const [businessFile, setBusinessFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState("");

  const [fieldErrors, setFieldErrors] = useState<{
    name?: string;
    email?: string;
    password?: string;
    passwordConfirm?: string;
  }>({});
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0] ?? null;
    if (file && file.type !== "application/pdf") {
      setBusinessFile(null);
      setFileError("PDF 파일만 업로드 가능합니다.");
      return;
    }
    setBusinessFile(file);
    setFileError("");
  }

  function handleStep1Next(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    const errors: typeof fieldErrors = {};
    if (!name.trim()) errors.name = "보호소 이름을 입력해 주세요.";
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) errors.email = "올바른 이메일 형식이 아닙니다.";
    if (!PW_REGEX.test(password)) errors.password = "영문+숫자+특수문자를 포함해 8자 이상 입력해 주세요.";
    if (password !== passwordConfirm) errors.passwordConfirm = "비밀번호가 일치하지 않습니다.";

    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      return;
    }
    setFieldErrors({});
    setStep(2);
    window.scrollTo({ top: 0 });
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (!businessFile) {
      setFileError("증빙 서류 PDF를 업로드해 주세요.");
      return;
    }

    setLoading(true);
    try {
      await signupShelter({
        name,
        email,
        password,
        business_registration_file: businessFile,
      });
      localStorage.setItem("pwa_welcome_pending", "1");
      router.replace(`/signup/verify-email?email=${encodeURIComponent(email)}`);
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
      <h2 className="text-[17px] font-bold text-gray-900">보호소 회원가입</h2>
    </header>
  );

  const approvalBanner = (
    <div className="flex items-start gap-2.5 rounded-xl bg-blue-50 px-4 py-3 mx-6 mt-3">
      <svg className="mt-0.5 shrink-0 text-blue-400" width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z" />
      </svg>
      <p className="text-[12px] leading-relaxed text-blue-600">
        관리자의 서류 검토 및 승인 후 회원가입이 완료됩니다.
      </p>
    </div>
  );

  // ── 1단계: 기본 정보 ──────────────────────────────────────────────────────────

  if (step === 1) {
    return (
      <main className="flex min-h-screen flex-col bg-white">
        {header}
        {approvalBanner}
        <StepIndicator current={1} />

        <div className="flex flex-1 flex-col px-6 pb-8">
          <p className="mb-5 text-[13px] text-gray-400">기본 정보를 입력해 주세요.</p>

          <form onSubmit={handleStep1Next} noValidate className="flex flex-1 flex-col gap-3.5 animate-slide-up">
            {/* 보호소 이름 */}
            <div className="space-y-1.5">
              <label htmlFor="name" className="block text-[13px] font-semibold text-gray-500">보호소 이름</label>
              <input
                id="name" name="name" type="text" autoComplete="organization" required
                value={name} onChange={(e) => { setName(e.target.value); setFieldErrors((prev) => ({ ...prev, name: undefined })); }}
                placeholder="보호소 이름을 입력해 주세요"
                className={`${INPUT} ${fieldErrors.name ? "border-red-400 focus:border-red-400" : ""}`}
              />
              {fieldErrors.name && <p className="text-[12px] text-red-500">{fieldErrors.name}</p>}
            </div>

            {/* 이메일 */}
            <div className="space-y-1.5">
              <label htmlFor="email" className="block text-[13px] font-semibold text-gray-500">이메일</label>
              <input
                id="email" name="email" type="email" autoComplete="email" required
                value={email} onChange={(e) => { setEmail(e.target.value); setFieldErrors((prev) => ({ ...prev, email: undefined })); }}
                placeholder="이메일 주소를 입력해 주세요"
                className={`${INPUT} ${fieldErrors.email ? "border-red-400 focus:border-red-400" : ""}`}
              />
              {fieldErrors.email && <p className="text-[12px] text-red-500">{fieldErrors.email}</p>}
            </div>

            {/* 비밀번호 */}
            <div className="space-y-1.5">
              <label htmlFor="password" className="block text-[13px] font-semibold text-gray-500">비밀번호</label>
              <div className="relative">
                <input
                  id="password" name="password"
                  type={showPw ? "text" : "password"}
                  autoComplete="new-password" required
                  value={password} onChange={(e) => { setPassword(e.target.value); setFieldErrors((prev) => ({ ...prev, password: undefined })); }}
                  placeholder="영문+숫자+특수문자를 포함해 주세요"
                  className={`${INPUT} pr-12 ${fieldErrors.password ? "border-red-400 focus:border-red-400" : ""}`}
                />
                <button type="button" tabIndex={-1} onClick={() => setShowPw((v) => !v)}
                  aria-label={showPw ? "비밀번호 숨기기" : "비밀번호 보기"}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                  <EyeIcon visible={showPw} />
                </button>
              </div>
              {fieldErrors.password && <p className="text-[12px] text-red-500">{fieldErrors.password}</p>}
            </div>

            {/* 비밀번호 확인 */}
            <div className="space-y-1.5">
              <label htmlFor="passwordConfirm" className="block text-[13px] font-semibold text-gray-500">비밀번호 확인</label>
              <div className="relative">
                <input
                  id="passwordConfirm" name="passwordConfirm"
                  type={showPwConfirm ? "text" : "password"}
                  autoComplete="new-password" required
                  value={passwordConfirm} onChange={(e) => { setPasswordConfirm(e.target.value); setFieldErrors((prev) => ({ ...prev, passwordConfirm: undefined })); }}
                  placeholder="비밀번호를 다시 입력해 주세요"
                  className={`${INPUT} pr-12 ${fieldErrors.passwordConfirm ? "border-red-400 focus:border-red-400" : ""}`}
                />
                <button type="button" tabIndex={-1} onClick={() => setShowPwConfirm((v) => !v)}
                  aria-label={showPwConfirm ? "비밀번호 숨기기" : "비밀번호 보기"}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                  <EyeIcon visible={showPwConfirm} />
                </button>
              </div>
              {fieldErrors.passwordConfirm && <p className="text-[12px] text-red-500">{fieldErrors.passwordConfirm}</p>}
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

  // ── 2단계: 증빙 서류 ──────────────────────────────────────────────────────────

  return (
    <main className="flex min-h-screen flex-col bg-white">
      {header}
      {approvalBanner}
      <StepIndicator current={2} />

      <div className="flex flex-1 flex-col px-6 pb-8">
        <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-4 animate-slide-up">
          <div className="space-y-1.5">
            <label className="block text-[13px] font-semibold text-gray-500">
              보호소 진위 확인 증빙 서류 <span className="font-normal text-gray-400">(PDF)</span>
            </label>
            <label
              htmlFor="businessFile"
              className={`flex cursor-pointer flex-col items-center justify-center gap-2.5 rounded-2xl border-2 border-dashed px-4 py-10 transition-colors ${
                fileError
                  ? "border-red-300 bg-red-50"
                  : businessFile
                  ? "border-orange-300 bg-orange-50"
                  : "border-gray-200 bg-gray-50 hover:border-orange-300 hover:bg-orange-50"
              }`}
            >
              {businessFile ? (
                <>
                  <svg className="text-orange-400" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                  </svg>
                  <p className="text-[13px] font-semibold text-orange-600 text-center break-all px-2">{businessFile.name}</p>
                  <p className="text-[11px] text-gray-400">파일을 변경하려면 다시 클릭하세요</p>
                </>
              ) : (
                <>
                  <svg className="text-gray-300" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="17 8 12 3 7 8" />
                    <line x1="12" y1="3" x2="12" y2="15" />
                  </svg>
                  <p className="text-[14px] font-medium text-gray-400">클릭하여 PDF 파일 업로드</p>
                </>
              )}
            </label>
            <input id="businessFile" type="file" accept="application/pdf" className="hidden" onChange={handleFileChange} />
            {fileError && <p className="text-[12px] text-red-500">{fileError}</p>}
            <p className="text-[11px] text-gray-400 leading-relaxed pt-1">
              공식 보호소 확인 후 서비스 이용이 가능합니다.<br />준비하신 증빙 서류를 위에 업로드해 주세요.
              <br />(동물보호센터 지정서, 동물보호시설 신고확인증 등)
            </p>
          </div>

          {error && <ErrorBox message={error} />}

          <div className="mt-auto pt-2">
            <button type="submit" disabled={loading}
              className="h-14 w-full rounded-2xl bg-orange-500 text-[15px] font-bold text-white shadow-md shadow-orange-100 transition-all duration-150 active:scale-[0.97] disabled:bg-gray-100 disabled:text-gray-400 disabled:shadow-none">
              {loading ? (
                <span className="flex items-center justify-center gap-2.5">
                  <Spinner />
                  신청 중...
                </span>
              ) : (
                "가입 신청하기"
              )}
            </button>
          </div>
        </form>
      </div>
    </main>
  );
}
