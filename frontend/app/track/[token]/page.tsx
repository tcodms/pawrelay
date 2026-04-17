"use client";

// 입양자 실시간 이송 현황 페이지 (로그인 불필요)
// TODO: GET /posts/public/{share_token} API 연동 및 WebSocket 실시간 업데이트 구현

import { useParams } from "next/navigation";
import { MapPin } from "lucide-react";

export default function TrackPage() {
  const params = useParams();
  const token = params.token as string;

  void token; // TODO: API 호출 시 사용

  return (
    <main className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-6 gap-4">
      <div className="flex h-14 w-14 items-center justify-center rounded-full bg-[#FDF3EC]">
        <MapPin size={28} className="text-[#EEA968]" />
      </div>
      <p className="text-[18px] font-bold text-gray-800">이송 현황 추적</p>
      <p className="text-[13px] text-gray-400 text-center leading-relaxed">
        실시간 이송 현황 페이지입니다.
        <br />
        현재 구현 중입니다.
      </p>
    </main>
  );
}
