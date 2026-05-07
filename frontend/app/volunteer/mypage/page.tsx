"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { User, Mail, LogOut } from "lucide-react";
import VolunteerHeader from "@/components/VolunteerHeader";
import { request, logout } from "@/lib/api";

interface Me {
  id: number;
  name: string;
  email: string;
  role: string;
}

export default function MyPage() {
  const router = useRouter();
  const [me, setMe] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);
  const [loggingOut, setLoggingOut] = useState(false);

  useEffect(() => {
    request<Me>("/auth/me")
      .then(setMe)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  async function handleLogout() {
    setLoggingOut(true);
    try {
      await logout();
      router.push("/login");
    } catch {
      setLoggingOut(false);
    }
  }

  return (
    <main className="min-h-screen bg-gray-50">
      <VolunteerHeader title="프로필" />

      {loading ? (
        <div className="flex justify-center pt-20">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-[#EEA968] border-t-transparent" />
        </div>
      ) : (
        <div className="mx-auto max-w-2xl px-4 pt-6 pb-24 space-y-3">

          {/* 프로필 카드 */}
          <div className="rounded-2xl bg-white border border-gray-100 shadow-sm px-5 py-5 space-y-4">
            <div className="flex items-center gap-4">
              <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-[#FDF3EC]">
                <User size={26} className="text-[#EEA968]" />
              </div>
              <div>
                <p className="text-[18px] font-bold text-gray-900">{me?.name ?? "-"}</p>
                <p className="text-[12px] text-gray-400 mt-0.5">봉사자</p>
              </div>
            </div>

            <div className="border-t border-gray-50 pt-4 space-y-3">
              <div className="flex items-center gap-3">
                <Mail size={15} className="text-gray-400 shrink-0" />
                <span className="text-[14px] text-gray-600">{me?.email ?? "-"}</span>
              </div>
            </div>
          </div>

          {/* 로그아웃 */}
          <button
            onClick={handleLogout}
            disabled={loggingOut}
            className="w-full flex items-center justify-between rounded-2xl bg-white border border-gray-100 shadow-sm px-5 py-4 active:scale-[0.98] transition-transform disabled:opacity-50"
          >
            <div className="flex items-center gap-3">
              <LogOut size={16} className="text-red-400" />
              <span className="text-[14px] font-semibold text-red-400">로그아웃</span>
            </div>
          </button>

        </div>
      )}
    </main>
  );
}
