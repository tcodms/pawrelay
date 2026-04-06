"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ClipboardList, MessageCircle, PawPrint, User } from "lucide-react";

const TABS = [
  {
    href: "/volunteer/posts",
    label: "공고",
    icon: ClipboardList,
  },
  {
    href: "/volunteer/chat",
    label: "채팅방",
    icon: MessageCircle,
  },
  {
    href: "/volunteer/services",
    label: "봉사내역",
    icon: PawPrint,
  },
  {
    href: "/volunteer/mypage",
    label: "마이페이지",
    icon: User,
  },
] as const;

export default function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 border-t border-gray-100 bg-white/95 backdrop-blur-sm">
      <ul className="flex h-16 items-stretch">
        {TABS.map(({ href, label, icon: Icon }) => {
          const active = pathname.startsWith(href);
          return (
            <li key={href} className="flex flex-1">
              <Link
                href={href}
                className="flex flex-1 flex-col items-center justify-center gap-0.5 transition-colors"
              >
                <Icon
                  size={22}
                  strokeWidth={active ? 2.5 : 1.8}
                  className={active ? "text-orange-500" : "text-gray-400"}
                />
                <span
                  className={`text-[10px] font-semibold ${
                    active ? "text-orange-500" : "text-gray-400"
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
