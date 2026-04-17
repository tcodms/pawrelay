"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter, useParams } from "next/navigation";
import { ArrowLeft, ArrowRight, MapPin, Calendar, PawPrint } from "lucide-react";
import {
  sendChatbotMessage,
  getChatbotSession,
  CHATBOT_SESSION_KEY,
} from "@/lib/api/chatbot";
import type { ChatbotResponse } from "@/lib/api/chatbot";
import { ApiError } from "@/lib/api";

// ── 타입 ──────────────────────────────────────────────────────────────────────

interface Message {
  role: "bot" | "user";
  text: string;
}

type AutoFilled = ChatbotResponse["auto_filled"];

// ── 상수 ──────────────────────────────────────────────────────────────────────

const SIZE_LABEL: Record<string, string> = {
  small: "소형 (5kg 이하)",
  medium: "중형 (5~15kg)",
  large: "대형 (15kg 이상)",
};

const TODAY = new Date().toISOString().split("T")[0];

// ── 공고 요약 카드 ─────────────────────────────────────────────────────────────

function PostSummaryCard({ autoFilled }: { autoFilled: NonNullable<AutoFilled> }) {
  return (
    <div className="mx-4 mt-3 mb-1 rounded-2xl bg-[#FDF3EC] border border-[#EEA968]/20 px-4 py-3 flex flex-col gap-1.5">
      <p className="text-[11px] font-bold text-[#EEA968] uppercase tracking-wide">신청 공고</p>
      {(autoFilled.post_origin || autoFilled.post_destination) && (
        <div className="flex items-center gap-1.5 text-[13px] text-[#7A4A28] font-semibold">
          <MapPin size={12} className="text-[#EEA968] shrink-0" />
          <span>{autoFilled.post_origin}</span>
          <ArrowRight size={11} className="text-[#EEA968] shrink-0" />
          <span>{autoFilled.post_destination}</span>
        </div>
      )}
      {autoFilled.available_date && (
        <div className="flex items-center gap-1.5 text-[12px] text-gray-500">
          <Calendar size={11} className="text-[#EEA968] shrink-0" />
          <span>{autoFilled.available_date}</span>
        </div>
      )}
      {autoFilled.max_animal_size && (
        <div className="flex items-center gap-1.5 text-[12px] text-gray-500">
          <PawPrint size={11} className="text-[#EEA968] shrink-0" />
          <span>{SIZE_LABEL[autoFilled.max_animal_size] ?? autoFilled.max_animal_size}</span>
        </div>
      )}
    </div>
  );
}

// ── 주소 검색 모달 ─────────────────────────────────────────────────────────────

function AddressModal({
  onSelect,
  onClose,
}: {
  onSelect: (address: string) => void;
  onClose: () => void;
}) {
  // TODO: 카카오 주소 검색 SDK 연동 (현재 텍스트 입력 placeholder)
  const [value, setValue] = useState("");

  return (
    <div className="fixed inset-0 z-50 flex items-end">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative z-10 w-full rounded-t-3xl bg-white px-5 pt-4 pb-10">
        <div className="flex justify-center mb-4">
          <div className="h-1 w-10 rounded-full bg-gray-200" />
        </div>
        <p className="text-[16px] font-bold text-gray-900 mb-4">주소 검색</p>
        {/* TODO: 여기에 카카오 주소 검색 iframe 삽입 */}
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="예: 광주광역시 북구"
          className="h-12 w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 text-[14px] text-gray-700 placeholder:text-gray-400 focus:outline-none focus:border-[#EEA968]/60"
          autoFocus
        />
        <button
          onClick={() => { if (value.trim()) onSelect(value.trim()); }}
          disabled={!value.trim()}
          className="mt-3 h-12 w-full rounded-full bg-[#EEA968] text-[14px] font-bold text-white disabled:opacity-40"
        >
          선택
        </button>
      </div>
    </div>
  );
}

// ── 페이지 ────────────────────────────────────────────────────────────────────

export default function ChatRoomPage() {
  const router = useRouter();
  const params = useParams();
  const sessionId = params.session_id as string;

  const [messages, setMessages] = useState<Message[]>([]);
  const [inputType, setInputType] = useState<ChatbotResponse["input_type"]>(null);
  const [options, setOptions] = useState<string[] | null>(null);
  const [autoFilled, setAutoFilled] = useState<AutoFilled>(null);
  const [completed, setCompleted] = useState(false);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [showAddressModal, setShowAddressModal] = useState(false);

  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    restoreSession();
  }, [sessionId]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function restoreSession() {
    try {
      const res = await getChatbotSession(sessionId);
      setMessages([{ role: "bot", text: res.message }]);
      setInputType(res.input_type);
      setOptions(res.options);
      setAutoFilled(res.auto_filled);
    } catch (err) {
      if (err instanceof ApiError && err.code === "SESSION_EXPIRED") {
        sessionStorage.removeItem(CHATBOT_SESSION_KEY);
        setMessages([{ role: "bot", text: "세션이 만료되었습니다. 새로 시작해 주세요." }]);
      } else {
        setMessages([{ role: "bot", text: "채팅을 불러올 수 없습니다." }]);
      }
    } finally {
      setLoading(false);
    }
  }

  async function sendMessage(userText: string) {
    setMessages((prev) => [...prev, { role: "user", text: userText }]);
    setSending(true);
    setInputType(null);
    try {
      const res = await sendChatbotMessage({
        session_id: sessionId,
        post_id: null,
        message: userText,
      });
      setMessages((prev) => [...prev, { role: "bot", text: res.message }]);
      setInputType(res.input_type);
      setOptions(res.options);
      if (res.auto_filled) setAutoFilled(res.auto_filled);
      if (res.completed) {
        setCompleted(true);
        sessionStorage.removeItem(CHATBOT_SESSION_KEY);
      }
    } catch (err) {
      const code = err instanceof ApiError ? err.code : "UNKNOWN_ERROR";
      const errorMessages: Record<string, string> = {
        GEOCODING_FAILED: "주소를 찾을 수 없어요. 다시 입력해 주세요.",
        SCHEDULE_SAVE_FAILED: "저장에 실패했어요. 다시 시도해 주세요.",
        SESSION_EXPIRED: "세션이 만료되었어요. 처음부터 다시 시작해 주세요.",
      };
      setMessages((prev) => [
        ...prev,
        { role: "bot", text: errorMessages[code] ?? "오류가 발생했어요. 다시 시도해 주세요." },
      ]);
      // 에러 시 이전 input_type 복원 (state 유지)
      const res = await getChatbotSession(sessionId).catch(() => null);
      if (res) { setInputType(res.input_type); setOptions(res.options); }
    } finally {
      setSending(false);
    }
  }

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-white">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-[#EEA968] border-t-transparent" />
      </main>
    );
  }

  return (
    <main className="flex min-h-screen flex-col bg-gray-50">

      {/* 헤더 */}
      <header className="sticky top-0 z-10 flex items-center gap-3 bg-white border-b border-gray-100 px-4 py-4">
        <button
          onClick={() => router.back()}
          className="flex h-9 w-9 items-center justify-center rounded-xl text-gray-500 hover:bg-gray-100 transition-colors"
          aria-label="뒤로 가기"
        >
          <ArrowLeft size={20} />
        </button>
        <div>
          <p className="text-[16px] font-bold text-gray-900 leading-tight">동선 등록 챗봇</p>
          <p className="text-[11px] text-gray-400">AI가 동선을 등록해 드려요</p>
        </div>
      </header>

      {/* 공고 요약 카드 (auto_filled 있을 때 고정 표시) */}
      {autoFilled && <PostSummaryCard autoFilled={autoFilled} />}

      {/* 메시지 목록 */}
      <div className="flex-1 overflow-y-auto px-4 py-4 flex flex-col gap-3 pb-40">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            {msg.role === "bot" && (
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#FDF3EC] mr-2 mt-0.5">
                <span className="text-[14px]">🐾</span>
              </div>
            )}
            <div
              className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-[14px] leading-relaxed ${
                msg.role === "bot"
                  ? "bg-white text-gray-800 shadow-sm border border-gray-100 rounded-tl-sm"
                  : "bg-[#EEA968] text-white rounded-tr-sm"
              }`}
            >
              {msg.text}
            </div>
          </div>
        ))}

        {/* 전송 중 로딩 */}
        {sending && (
          <div className="flex justify-start">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#FDF3EC] mr-2">
              <span className="text-[14px]">🐾</span>
            </div>
            <div className="bg-white border border-gray-100 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm flex gap-1 items-center">
              <span className="h-2 w-2 rounded-full bg-gray-300 animate-bounce [animation-delay:0ms]" />
              <span className="h-2 w-2 rounded-full bg-gray-300 animate-bounce [animation-delay:150ms]" />
              <span className="h-2 w-2 rounded-full bg-gray-300 animate-bounce [animation-delay:300ms]" />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* 입력 영역 */}
      {!completed && !sending && inputType && (
        <div className="fixed bottom-16 left-0 right-0 z-20 bg-white border-t border-gray-100 px-4 py-3">

          {/* buttons */}
          {inputType === "buttons" && options && (
            <div className="flex flex-col gap-2">
              {options.map((opt) => (
                <button
                  key={opt}
                  onClick={() => sendMessage(opt)}
                  className={`h-12 w-full rounded-full border-2 text-[14px] font-semibold transition-all active:scale-[0.97] ${
                    opt === "처음부터 다시"
                      ? "border-gray-200 text-gray-500 hover:bg-gray-50"
                      : "border-[#EEA968] text-[#EEA968] hover:bg-[#FDF3EC]"
                  }`}
                >
                  {opt}
                </button>
              ))}
            </div>
          )}

          {/* date_picker */}
          {inputType === "date_picker" && (
            <div className="flex gap-2">
              <input
                type="date"
                min={TODAY}
                defaultValue={TODAY}
                id="date-picker"
                className="flex-1 h-12 rounded-2xl border border-gray-200 bg-gray-50 px-4 text-[14px] text-gray-700 focus:outline-none focus:border-[#EEA968]/60"
              />
              <button
                onClick={() => {
                  const el = document.getElementById("date-picker") as HTMLInputElement;
                  if (el?.value) sendMessage(el.value);
                }}
                className="h-12 px-5 rounded-full bg-[#EEA968] text-[14px] font-bold text-white active:scale-95"
              >
                선택
              </button>
            </div>
          )}

          {/* address_search */}
          {inputType === "address_search" && (
            <button
              onClick={() => setShowAddressModal(true)}
              className="h-12 w-full rounded-full border-2 border-[#EEA968] text-[14px] font-semibold text-[#EEA968] hover:bg-[#FDF3EC] transition-colors active:scale-[0.97]"
            >
              주소 검색하기
            </button>
          )}
        </div>
      )}

      {/* COMPLETED */}
      {completed && (
        <div className="fixed bottom-16 left-0 right-0 z-20 bg-white border-t border-gray-100 px-4 py-3">
          <button
            onClick={() => router.replace("/volunteer/chat")}
            className="h-12 w-full rounded-full bg-[#EEA968] text-[14px] font-bold text-white shadow-md shadow-[#EEA968]/20 active:scale-[0.97]"
          >
            채팅 목록으로
          </button>
        </div>
      )}

      {/* 주소 검색 모달 */}
      {showAddressModal && (
        <AddressModal
          onSelect={(address) => {
            setShowAddressModal(false);
            sendMessage(address);
          }}
          onClose={() => setShowAddressModal(false)}
        />
      )}
    </main>
  );
}
