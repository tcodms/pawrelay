import type { Metadata, Viewport } from "next";
import { Fredoka, Noto_Sans_KR } from "next/font/google";
import dynamic from "next/dynamic";
import "./globals.css";

const SplashScreen = dynamic(() => import("@/components/SplashScreen"), { ssr: false });

// 영문 로고용
const fredoka = Fredoka({
  subsets: ["latin"],
  weight: ["600", "700"],
  variable: "--font-fredoka",
  display: "swap",
});

// 한글 본문용 — 깔끔하고 현대적인 산세리프
const notoSansKr = Noto_Sans_KR({
  weight: ["400", "500", "700"],
  subsets: ["latin"],
  variable: "--font-noto",
  display: "swap",
  preload: false,
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
  themeColor: "#F97316",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko" className={`${fredoka.variable} ${notoSansKr.variable}`}>
      <head>
        <link rel="apple-touch-icon" href="/icons/apple-touch-icon.png" />
        <meta name="mobile-web-app-capable" content="yes" />
      </head>
      <body className="bg-white text-gray-900 antialiased font-[family-name:var(--font-noto)]">
        <SplashScreen />
        {children}
      </body>
    </html>
  );
}
