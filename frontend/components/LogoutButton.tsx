"use client";

import { useRouter } from "next/navigation";
import { LogOut } from "lucide-react";
import { logout } from "@/lib/api";

export default function LogoutButton() {
  const router = useRouter();

  async function handleLogout() {
    try {
      await logout();
    } finally {
      router.push("/login");
    }
  }

  return (
    <button
      onClick={handleLogout}
      aria-label="로그아웃"
      className="fixed top-4 right-4 z-50 flex h-8 w-8 items-center justify-center rounded-full bg-white/80 backdrop-blur-sm border border-gray-200 shadow-sm text-gray-400 hover:text-gray-600 transition-colors"
    >
      <LogOut size={15} />
    </button>
  );
}
