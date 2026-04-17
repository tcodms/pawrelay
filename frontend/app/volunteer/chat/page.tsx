"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { CHATBOT_SESSION_KEY } from "@/lib/api/chatbot";

// ── 더미 채팅방 목록 ───────────────────────────────────────────────────────────

interface ChatRoom {
  session_id: string;
  title: string;
  last_message: string;
  time: string;
  unread: number;
  // post_id 있는 진입은 동물 사진, 없는 직접 진입은 null (봇 아이콘 표시)
  animal_photo_url: string | null;
}

const DUMMY_ROOMS: ChatRoom[] = [
  {
    session_id: "session-001",
    title: "[초코] 릴레이 지원",
    last_message: "출발지를 광주광역시 북구로 등록했어요. 차량이 있으신가요?",
    time: "오후 2:30",
    unread: 2,
    animal_photo_url: "https://images.unsplash.com/photo-1552053831-71594a27632d?w=200",
  },
  {
    session_id: "session-002",
    title: "동선 등록",
    last_message: "동선이 성공적으로 등록되었어요. 매칭 결과를 기다려 주세요!",
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

  return (
    <main className="min-h-screen bg-white">
      {/* 헤더 */}
      <header className="sticky top-0 z-10 bg-white border-b border-gray-100 px-5 py-4 flex items-center justify-between">
        <h1 className="text-[20px] font-bold text-gray-900">채팅</h1>
        <button
          onClick={async () => {
            try {
              const { sendChatbotMessage, CHATBOT_SESSION_KEY } = await import("@/lib/api/chatbot");
              const res = await sendChatbotMessage({ session_id: null, post_id: null, message: null });
              sessionStorage.setItem(CHATBOT_SESSION_KEY, res.session_id);
              router.push(`/volunteer/chat/${res.session_id}`);
            } catch {
              alert("채팅을 시작할 수 없습니다. 다시 시도해 주세요.");
            }
          }}
          aria-label="새 동선 등록"
          className="flex h-9 w-9 items-center justify-center rounded-full bg-[#FDF3EC] text-[#EEA968] hover:bg-[#f0e0d0] transition-colors active:scale-95"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
            <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
          </svg>
        </button>
      </header>

      {/* 채팅방 목록 */}
      <ul>
        {DUMMY_ROOMS.map((room) => (
          <li key={room.session_id}>
            <button
              onClick={() => router.push(`/volunteer/chat/${room.session_id}`)}
              className="w-full flex items-center gap-4 px-5 py-4 border-b border-gray-100 active:bg-gray-50 transition-colors text-left"
            >
              {/* 프로필 사진 — 공고 연결 시 동물 사진, 직접 진입 시 봇 아이콘 */}
              <div className="relative shrink-0 h-14 w-14 rounded-full overflow-hidden bg-[#FDF3EC] flex items-center justify-center">
                {room.animal_photo_url ? (
                  <Image
                    src={room.animal_photo_url}
                    alt={room.title}
                    fill
                    className="object-cover"
                  />
                ) : (
                  <span className="text-2xl">🐾</span>
                )}
              </div>

              {/* 텍스트 */}
              <div className="flex-1 min-w-0">
                <p className="text-[15px] font-bold text-gray-900 mb-1 truncate">
                  {room.title}
                </p>
                <p className="text-[13px] text-gray-400 truncate leading-snug">
                  {room.last_message}
                </p>
              </div>

              {/* 시간 + 뱃지 */}
              <div className="flex flex-col items-end gap-1.5 shrink-0">
                <span className="text-[11px] text-gray-400">{room.time}</span>
                {room.unread > 0 && (
                  <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-red-500 px-1.5 text-[10px] font-bold text-white">
                    {room.unread}
                  </span>
                )}
              </div>
            </button>
          </li>
        ))}
      </ul>

    </main>
  );
}
