"use client";

import { useState, useEffect } from "react";

type State = "visible" | "fading" | "hidden";

export default function SplashScreen() {
  const [state, setState] = useState<State>("visible");

  useEffect(() => {
    // 클라이언트 내비게이션(SPA 이동)에서는 재표시 방지
    if (sessionStorage.getItem("splash_shown")) {
      setState("hidden");
      return;
    }

    const fadeTimer = setTimeout(() => setState("fading"), 1800);
    const hideTimer = setTimeout(() => {
      sessionStorage.setItem("splash_shown", "1");
      setState("hidden");
    }, 2400);

    return () => {
      clearTimeout(fadeTimer);
      clearTimeout(hideTimer);
    };
  }, []);

  if (state === "hidden") return null;

  return (
    <div
      aria-hidden="true"
      className={`fixed inset-0 z-[200] flex flex-col items-center justify-center bg-white transition-opacity duration-500 ${
        state === "fading" ? "pointer-events-none opacity-0" : "opacity-100"
      }`}
    >
      {/* 한글 문구 — Jua, 따뜻한 무채색 */}
      <p
        className="font-[family-name:var(--font-jua)] mb-3 text-center text-[14px] leading-relaxed text-stone-400 animate-fade-in"
      >
        새로운 가족으로 향하는 따뜻한 릴레이
      </p>

      {/* 영문 로고 — Fredoka */}
      <h1
        className="font-[family-name:var(--font-fredoka)] text-[56px] font-bold text-orange-500 leading-none animate-scale-in"
        style={{ animationDelay: "0.1s" }}
      >
        PawRelay
      </h1>
    </div>
  );
}
