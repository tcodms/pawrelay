import { NextResponse } from "next/server";

// 인증 토큰이 httpOnly 쿠키로 전달되므로 미들웨어에서 서버사이드 검증이 불가합니다.
// 보호 경로의 인증은 lib/api.ts의 401 → /auth/refresh → /login 리다이렉트 플로우에 위임합니다.
export function middleware() {
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|icons|manifest.json).*)"],
};
