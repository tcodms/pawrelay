import type { Metadata, Viewport } from "next";
import { Fredoka, Jua } from "next/font/google";
import dynamic from "next/dynamic";
import "./globals.css";

const SplashScreen = dynamic(() => import("@/components/SplashScreen"), { ssr: false });

// 영문 로고용 — Nunito보다 획 끝이 더 둥글고 귀여운 폰트
const fredoka = Fredoka({
  subsets: ["latin"],
  weight: ["600", "700"],
  variable: "--font-fredoka",
  display: "swap",
});

// 한글 문구용 — 획이 둥글고 아기자기한 한국어 폰트
const jua = Jua({
  weight: "400",
  subsets: ["latin"],
  variable: "--font-jua",
  display: "swap",
  preload: false, // 한글 폰트는 용량이 크므로 preload 비활성
});

export const metadata: Metadata = {
  title: "PawRelay",
  description: "유기동물 릴레이 이동봉사 플랫폼",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "PawRelay",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: "#F97316",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko" className={`${fredoka.variable} ${jua.variable}`}>
      <head>
        <link rel="apple-touch-icon" href="/icons/apple-touch-icon.png" />
        <meta name="mobile-web-app-capable" content="yes" />
      </head>
      <body className="bg-white text-gray-900 antialiased">
        <SplashScreen />
        {children}
      </body>
    </html>
  );
}
