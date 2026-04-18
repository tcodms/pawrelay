"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { MessageCircle, Plus, Bell } from "lucide-react";
import { CHATBOT_SESSION_KEY, CHATBOT_POST_CONTEXT_KEY } from "@/lib/api/chatbot";
import type { PostContext } from "@/lib/api/chatbot";

// ── 더미 채팅방 목록 ───────────────────────────────────────────────────────────

interface ChatRoom {
  session_id: string;
  title: string;
  last_message: string;
  time: string;
  unread: number;
  animal_photo_url: string | null;
  post_context?: PostContext;
}

const DUMMY_ROOMS: ChatRoom[] = [
  {
    session_id: "session-001",
    title: "[초코] 릴레이 지원",
    last_message: "수락 완료됐어요! 보호소 최종 확인 후 매칭이 확정돼요.",
    time: "오후 2:30",
    unread: 2,
    animal_photo_url: "https://images.unsplash.com/photo-1552053831-71594a27632d?w=200",
    post_context: {
      post_id: 1,
      animal_name: "초코",
      photo_url: "https://images.unsplash.com/photo-1552053831-71594a27632d?w=400",
      destination: "서울특별시 강남구",
      available_date: "2026-04-10",
      max_animal_size: "small",
    },
  },
  {
    session_id: "session-002",
    title: "릴레이 도우미",
    last_message: "봉사 정보가 등록되었어요! 매칭 제안 해드릴게요. 🐾",
    time: "어제",
    unread: 0,
    animal_photo_url: null,
  },
];

// ── 페이지 ────────────────────────────────────────────────────────────────────

export default function ChatPage() {
  const router = useRouter();

  useEffect(() => {
    const sessionId = sessionStorage.getItem(CHATBOT_SESSION_KEY);
    if (sessionId) {
      sessionStorage.removeItem(CHATBOT_SESSION_KEY);
      router.replace(`/volunteer/chat/${sessionId}`);
    }
  }, [router]);

  function startNewChat() {
    const sessionId = crypto.randomUUID();
    sessionStorage.removeItem(CHATBOT_POST_CONTEXT_KEY);
    router.push(`/volunteer/chat/${sessionId}`);
  }

  return (
    <main className="min-h-screen bg-gray-50">

      {/* 헤더 */}
      <header className="sticky top-0 z-10 bg-white border-b border-gray-100">
        <div className="mx-auto max-w-2xl px-5 pt-4 pb-3 flex items-center justify-between">
          <div>
            <h1 className="text-[18px] font-bold text-gray-900 leading-tight">채팅</h1>
            <p className="text-[11px] text-gray-400 mt-0.5">봉사를 시작해볼까요?</p>
          </div>
          <button className="flex h-8 w-8 items-center justify-center rounded-xl text-gray-400 hover:bg-gray-50 transition-colors">
            <Bell size={18} strokeWidth={1.8} />
          </button>
        </div>
      </header>

      {/* 채팅방 목록 */}
      <div className="mx-auto max-w-2xl">
      {DUMMY_ROOMS.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-3 pt-28 text-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-[#FDF3EC]">
            <MessageCircle size={28} className="text-[#EEA968]" />
          </div>
          <p className="text-[15px] font-bold text-gray-700">아직 대화가 없어요</p>
          <p className="text-[13px] text-gray-400">아래 버튼을 눌러 봉사를 시작해보세요!</p>
        </div>
      ) : (
        <ul className="px-4 pt-3 pb-4 space-y-2.5">
          {DUMMY_ROOMS.map((room) => (
            <li key={room.session_id}>
              <button
                onClick={() => {
                  if (room.post_context) {
                    sessionStorage.setItem(CHATBOT_POST_CONTEXT_KEY, JSON.stringify(room.post_context));
                  } else {
                    sessionStorage.removeItem(CHATBOT_POST_CONTEXT_KEY);
                  }
                  router.push(`/volunteer/chat/${room.session_id}`);
                }}
                className="w-full flex items-center gap-3.5 bg-white rounded-2xl px-4 py-3.5 border border-gray-100 shadow-sm active:scale-[0.98] transition-transform text-left"
              >
                {/* 프로필 */}
                <div className="relative shrink-0">
                  <div className="relative h-[52px] w-[52px] rounded-2xl overflow-hidden bg-gray-100 flex items-center justify-center">
                    {room.animal_photo_url ? (
                      <Image
                        src={room.animal_photo_url}
                        alt={room.title}
                        fill
                        className="object-cover rounded-2xl"
                      />
                    ) : (
                      <div className="h-full w-full flex items-center justify-center bg-gray-100">
                        <MessageCircle size={20} className="text-gray-300 fill-gray-300" />
                      </div>
                    )}
                  </div>
                  {room.unread > 0 && (
                    <span className="absolute -top-1 -right-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white shadow-sm">
                      {room.unread}
                    </span>
                  )}
                </div>

                {/* 텍스트 */}
                <div className="flex-1 min-w-0">
                  <p className={`text-[14px] font-bold mb-0.5 truncate ${room.unread > 0 ? "text-gray-900" : "text-gray-700"}`}>
                    {room.title}
                  </p>
                  <p className="text-[12px] text-gray-400 truncate leading-snug">
                    {room.last_message}
                  </p>
                </div>

                {/* 시간 */}
                <span className={`shrink-0 text-[11px] ${room.unread > 0 ? "text-[#EEA968] font-semibold" : "text-gray-400"}`}>
                  {room.time}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
      </div>

      {/* 플로팅 버튼 */}
      <div className="fixed bottom-20 left-0 right-0 flex justify-center z-20 pointer-events-none">
        <button
          onClick={startNewChat}
          className="pointer-events-auto flex items-center gap-2 h-12 px-6 rounded-full bg-[#EEA968] text-white text-[14px] font-bold shadow-lg shadow-[#EEA968]/30 active:scale-95 transition-transform"
        >
          <Plus size={18} strokeWidth={3} />
          봉사 시작하기
        </button>
      </div>

    </main>
  );
}
