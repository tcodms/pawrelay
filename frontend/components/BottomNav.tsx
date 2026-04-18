"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, MessageCircle, Route, User } from "lucide-react";

const TABS = [
  {
    href: "/volunteer",
    label: "홈",
    icon: Home,
    exact: true,
  },
  {
    href: "/volunteer/chat",
    label: "채팅",
    icon: MessageCircle,
    exact: false,
  },
  {
    href: "/volunteer/services",
    label: "내 릴레이",
    icon: Route,
    exact: false,
  },
  {
    href: "/volunteer/mypage",
    label: "프로필",
    icon: User,
    exact: false,
  },
] as const;

export default function BottomNav() {
  const pathname = usePathname();

  return (
    <nav aria-label="하단 내비게이션" className="fixed bottom-0 left-0 right-0 z-50 border-t border-gray-100 bg-white/95 backdrop-blur-sm">
      <ul className="flex h-16 items-stretch">
        {TABS.map(({ href, label, icon: Icon, exact }) => {
          const active = exact ? pathname === href : pathname.startsWith(href);
          return (
            <li key={href} className="flex flex-1">
              <Link
                href={href}
                aria-current={active ? "page" : undefined}
                className="flex flex-1 flex-col items-center justify-center gap-0.5 transition-colors"
              >
                <Icon
                  size={22}
                  strokeWidth={active ? 2.5 : 1.8}
                  className={active ? "text-[#EEA968]" : "text-gray-400"}
                />
                <span
                  className={`text-[9px] font-semibold ${
                    active ? "text-[#EEA968]" : "text-gray-400"
                  }`}
                >
                  {label}
                </span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
