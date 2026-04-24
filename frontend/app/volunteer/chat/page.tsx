"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { MessageCircle, Plus, Bell, CheckCircle2, X, Trash2 } from "lucide-react";
import { CHATBOT_SESSION_KEY, CHATBOT_POST_CONTEXT_KEY, sendChatMessage, getChatSessions, deleteChatSession } from "@/lib/api/chatbot";
import type { PostContext } from "@/lib/api/chatbot";
import type { AppNotification } from "@/lib/api/notifications";

// ── 채팅방 목록 ────────────────────────────────────────────────────────────────

interface ChatRoom {
  session_id: string;
  title: string;
  last_message: string;
  time: string;
  unread: number;
  animal_photo_url: string | null;
  post_context?: PostContext;
}

// ── 더미 알림 ─────────────────────────────────────────────────────────────────

const DUMMY_NOTIFICATIONS: AppNotification[] = [
  {
    id: 1,
    type: "matching_proposed",
    message: "새로운 매칭 제안이 도착했어요.",
    payload: { segment_id: 1, url: "/volunteer/matching/1", chat_session_id: "session-001" },
    created_at: "2026-04-10T09:00:00Z",
  },
  {
    id: 2,
    type: "matching_confirmed",
    message: "[초코] 매칭이 확정됐어요! 상세 내용을 확인하세요.",
    payload: { segment_id: 42, url: "/volunteer/matching/42", chat_session_id: "session-001" },
    created_at: "2026-04-09T15:30:00Z",
  },
];

const NOTIF_TYPE_LABEL: Record<string, string> = {
  matching_proposed: "매칭 제안",
  matching_confirmed: "매칭 확정",
  ping_check: "출발 확인",
  delay_reported: "지연 알림",
  sos_triggered: "SOS 발생",
  handover_waiting_confirm: "인계 대기",
  handover_location_changed: "장소 변경",
  matching_failed: "매칭 실패",
};

function formatRoomTime(isoString: string) {
  if (!isoString) return "";
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  if (diffHours < 1) return "방금 전";
  if (diffHours < 24) return `${diffHours}시간 전`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays === 1) return "어제";
  return `${diffDays}일 전`;
}

function formatNotifTime(isoString: string) {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  if (diffMs < 0) return "방금 전";
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  if (diffHours < 1) return "방금 전";
  if (diffHours < 24) return `${diffHours}시간 전`;
  return `${Math.floor(diffHours / 24)}일 전`;
}

// ── 페이지 ────────────────────────────────────────────────────────────────────

export default function ChatPage() {
  const router = useRouter();
  const [notifOpen, setNotifOpen] = useState(false);
  const [notifications, setNotifications] = useState<AppNotification[]>(DUMMY_NOTIFICATIONS);
  const [readIds, setReadIds] = useState<Set<number>>(new Set());
  const [rooms, setRooms] = useState<ChatRoom[]>([]);

  useEffect(() => {
    getChatSessions()
      .then((sessions) => {
        setRooms(sessions.map((s) => ({
          session_id: s.session_id,
          title: s.title,
          last_message: s.last_message || "대화를 시작해보세요.",
          time: formatRoomTime(s.updated_at),
          unread: 0,
          animal_photo_url: null,
        })));
      })
      .catch(() => setRooms([]));
  }, []);

  const unreadCount = notifications.filter((n) => !readIds.has(n.id)).length;

  function handleNotifClick(notif: AppNotification) {
    setReadIds((prev) => { const next = new Set(prev); next.add(notif.id); return next; });
    setNotifOpen(false);
    if (notif.payload.chat_session_id) {
      sessionStorage.setItem("matchingChatSession", notif.payload.chat_session_id);
    }
    if (notif.payload.url) {
      router.push(notif.payload.url);
    }
  }

  useEffect(() => {
    const sessionId = sessionStorage.getItem(CHATBOT_SESSION_KEY);
    if (sessionId) {
      sessionStorage.removeItem(CHATBOT_SESSION_KEY);
      router.replace(`/volunteer/chat/${sessionId}`);
    }
  }, [router]);

  const [starting, setStarting] = useState(false);

  async function handleDeleteRoom(sessionId: string) {
    try {
      await deleteChatSession(sessionId);
      setRooms((prev) => prev.filter((r) => r.session_id !== sessionId));
    } catch {
      alert("삭제에 실패했어요. 다시 시도해 주세요.");
    }
  }

  async function startNewChat() {
    if (starting) return;
    setStarting(true);
    try {
      sessionStorage.removeItem(CHATBOT_POST_CONTEXT_KEY);
      const res = await sendChatMessage(null, null, null);
      sessionStorage.setItem(`chatbot_init_${res.session_id}`, JSON.stringify(res));
      router.push(`/volunteer/chat/${res.session_id}`);
    } catch {
      alert("채팅을 시작할 수 없습니다. 다시 시도해 주세요.");
    } finally {
      setStarting(false);
    }
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
          <button
            onClick={() => setNotifOpen(true)}
            className="relative flex h-8 w-8 items-center justify-center rounded-xl text-gray-400 hover:bg-gray-50 transition-colors"
          >
            <Bell size={18} strokeWidth={1.8} />
            {unreadCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[9px] font-bold text-white">
                {unreadCount}
              </span>
            )}
          </button>
        </div>
      </header>

      {/* 채팅방 목록 */}
      <div className="mx-auto max-w-2xl">
      {rooms.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-3 pt-28 text-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-[#FDF3EC]">
            <MessageCircle size={28} className="text-[#EEA968]" />
          </div>
          <p className="text-[15px] font-bold text-gray-700">아직 대화가 없어요</p>
          <p className="text-[13px] text-gray-400">아래 버튼을 눌러 봉사를 시작해보세요!</p>
        </div>
      ) : (
        <ul className="px-4 pt-3 pb-4 space-y-2.5">
          {rooms.map((room) => (
            <li key={room.session_id} className="flex items-center gap-2">
              <button
                onClick={() => {
                  if (room.post_context) {
                    sessionStorage.setItem(CHATBOT_POST_CONTEXT_KEY, JSON.stringify(room.post_context));
                  } else {
                    sessionStorage.removeItem(CHATBOT_POST_CONTEXT_KEY);
                  }
                  router.push(`/volunteer/chat/${room.session_id}`);
                }}
                className="flex-1 flex items-center gap-3.5 bg-white rounded-2xl px-4 py-3.5 border border-gray-100 shadow-sm active:scale-[0.98] transition-transform text-left"
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
              <button
                onClick={() => handleDeleteRoom(room.session_id)}
                className="shrink-0 flex h-9 w-9 items-center justify-center rounded-xl text-gray-300 hover:text-red-400 hover:bg-red-50 transition-colors"
                aria-label="세션 삭제"
              >
                <Trash2 size={16} />
              </button>
            </li>
          ))}
        </ul>
      )}
      </div>

      {/* 알림 패널 */}
      {notifOpen && (
        <div className="fixed inset-0 z-50 flex items-start">
          <div
            className="absolute inset-0 bg-black/40"
            onClick={() => setNotifOpen(false)}
          />
          <div className="relative w-full bg-white rounded-b-3xl max-w-2xl mx-auto max-h-screen flex flex-col">
            <div className="flex items-center justify-between px-5 pt-5 pb-3 shrink-0">
              <div>
                <p className="text-[16px] font-bold text-gray-900">알림</p>
                {unreadCount > 0 && (
                  <p className="text-[12px] text-[#EEA968] font-semibold">{unreadCount}개의 새 알림</p>
                )}
              </div>
              <button
                onClick={() => setNotifOpen(false)}
                className="flex h-8 w-8 items-center justify-center rounded-xl text-gray-400 hover:bg-gray-100"
              >
                <X size={18} />
              </button>
            </div>
            <div className="overflow-y-auto pb-8">
              {notifications.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-gray-400">
                  <Bell size={28} strokeWidth={1.5} className="mb-2" />
                  <p className="text-[14px]">새 알림이 없어요</p>
                </div>
              ) : (
                <ul className="px-4 space-y-2 pb-2">
                  {notifications.map((notif) => {
                    const isRead = readIds.has(notif.id);
                    return (
                      <li key={notif.id}>
                        <button
                          onClick={() => handleNotifClick(notif)}
                          className="w-full flex items-start gap-3 rounded-2xl px-4 py-3.5 text-left transition-colors active:scale-[0.98] bg-gray-50"
                        >
                          <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${isRead ? "bg-gray-200" : "bg-[#EEA968]"}`}>
                            <CheckCircle2 size={14} className={isRead ? "text-gray-400" : "text-white"} />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-1.5 mb-0.5">
                              <span className={`text-[11px] font-bold ${isRead ? "text-gray-400" : "text-[#EEA968]"}`}>
                                {NOTIF_TYPE_LABEL[notif.type] ?? notif.type}
                              </span>
                              {!isRead && (
                                <span className="h-1.5 w-1.5 rounded-full bg-[#EEA968]" />
                              )}
                            </div>
                            <p className={`text-[13px] leading-snug ${isRead ? "text-gray-500" : "text-gray-800 font-medium"}`}>
                              {notif.message}
                            </p>
                            <p className="text-[11px] text-gray-400 mt-1">{formatNotifTime(notif.created_at)}</p>
                          </div>
                        </button>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 플로팅 버튼 */}
      <div className="fixed bottom-20 left-0 right-0 flex justify-center z-20 pointer-events-none">
        <button
          onClick={startNewChat}
          disabled={starting}
          className="pointer-events-auto flex items-center gap-2 h-12 px-6 rounded-full bg-[#EEA968] text-white text-[14px] font-bold shadow-lg shadow-[#EEA968]/30 active:scale-95 transition-transform disabled:opacity-60"
        >
          {starting ? (
            <div className="h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
          ) : (
            <Plus size={18} strokeWidth={3} />
          )}
          봉사 시작하기
        </button>
      </div>

    </main>
  );
}
