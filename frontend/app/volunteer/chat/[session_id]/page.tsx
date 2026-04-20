"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter, useParams } from "next/navigation";
import Image from "next/image";
import {
  ArrowLeft, ArrowRight, ArrowUp, MapPin, Calendar, PawPrint,
  CheckCircle2, ExternalLink, Users, MessageCircle,
} from "lucide-react";
import {
  sendChatMessage,
  CHATBOT_SESSION_KEY,
  CHATBOT_POST_CONTEXT_KEY,
} from "@/lib/api/chatbot";
import type { PostContext, PostSuggestion } from "@/lib/api/chatbot";
import { getUnreadNotifications, markNotificationRead } from "@/lib/api/notifications";
import type { AppNotification } from "@/lib/api/notifications";

// ── 메시지 타입 ───────────────────────────────────────────────────────────────

type Message =
  | { role: "bot" | "user"; type: "text"; text: string }
  | { role: "bot"; type: "post_card"; post: PostSuggestion }
  | { role: "bot"; type: "recommendation"; rec: RecommendedPost }
  | { role: "bot"; type: "matching_confirmed"; info: MatchingInfo }
  | { role: "bot"; type: "matching_reason"; reason: string; chain: ChainSegment[] }
  | { role: "bot"; type: "ping_check"; segment_id: number; animal_name: string; depart_time: string; from: string }
  | { role: "bot"; type: "notification"; notif_id: number; notif_type: string; message: string; segment_id?: number; url?: string };

interface RecommendedPost {
  post_id: number;
  segment_id: number;
  animal_name: string;
  photo_url?: string;
  size: "small" | "medium" | "large";
  origin: string;
  destination: string;
  scheduled_date: string;
  current_volunteers: number;
  needed_volunteers: number;
}

interface ChainSegment {
  volunteer: string;
  from: string;
  to: string;
  isMe?: boolean;
}

interface MatchingInfo {
  segment_id: number;
  animal_name: string;
  photo_url?: string;
  size: "small" | "medium" | "large";
  my_segment: { from: string; to: string };
  scheduled_date: string;
  depart_time: string;
  estimated_arrival_time?: string;
  open_chat_url: string;
  handover_candidates: HandoverCandidate[];
  prev_volunteer?: string;
  next_volunteer?: string;
}

interface HandoverCandidate {
  name: string;
  type: "station" | "rest_area" | "terminal";
  distance_km: number;
}

// ── 상수 ──────────────────────────────────────────────────────────────────────

const SIZE_LABEL: Record<string, string> = {
  small: "소형",
  medium: "중형",
  large: "대형",
};


// ── 더미 대화 (session-001 전용 — CONFIRM 이전) ──────────────────────────────

const DEMO_MESSAGES_1_PRE: Message[] = [
  {
    role: "bot", type: "text",
    text: "초코 릴레이 봉사를 신청해 주셔서 감사해요! 🐾\n도착지·날짜·동물 크기는 공고에서 확인했어요.\n출발 가능한 지역과 차량 유무를 알려주세요.",
  },
  {
    role: "bot", type: "post_card",
    post: {
      post_id: 1,
      animal_name: "초코",
      photo_url: "https://images.unsplash.com/photo-1552053831-71594a27632d?w=400",
      origin: "광주광역시 북구",
      destination: "서울특별시 강남구",
      scheduled_date: "2026-04-10",
      max_animal_size: "small",
    },
  },
  { role: "user", type: "text", text: "광주에서 출발 가능해. 차도 있어!" },
  {
    role: "bot", type: "text",
    text: "알겠어요! 출발 예정 시간과 목적지 도착 예정 시간도 알려주세요.\n예) 09:00 출발 → 10:40 도착 예정",
  },
  { role: "user", type: "text", text: "09시에 출발해서 10시 40분쯤 도착할 것 같아" },
  {
    role: "bot", type: "text",
    text: "감사합니다! 아래 내용으로 동선을 등록할까요?\n\n출발지: 광주광역시\n도착지: 서울특별시 강남구\n날짜: 2026-04-10\n차량: 있음\n최대 동물 크기: 소형 (5kg 이하)\n출발 시간: 09:00\n도착 예정: 10:40",
  },
];

// ── 더미 대화 (session-001 — 동선 등록 후 매칭 제안) ─────────────────────────

const DEMO_MESSAGES_1_POST: Message[] = [
  {
    role: "bot", type: "text",
    text: "봉사 정보가 등록됐어요! 매칭 제안 해드릴게요. 🐾",
  },
  {
    role: "bot", type: "text",
    text: "동선을 분석해 봤어요. 딱 맞는 구간이 있네요 😊",
  },
  {
    role: "bot", type: "matching_reason",
    reason: "출발지(광주광역시 북구)가 공고 출발지와 일치하고, 차량이 있어 소형 동물 수송에 최적입니다. 천안역에서 다음 봉사자와 인계가 원활하게 이루어질 수 있어 이 구간을 추천드려요.",
    chain: [
      { volunteer: "나 (김봉사)", from: "광주광역시 북구", to: "천안역", isMe: true },
      { volunteer: "이릴레이", from: "천안역", to: "수원역" },
      { volunteer: "박도움", from: "수원역", to: "서울 강남구" },
    ],
  },
  {
    role: "bot", type: "recommendation",
    rec: {
      post_id: 1,
      segment_id: 1,
      animal_name: "초코",
      photo_url: "https://images.unsplash.com/photo-1552053831-71594a27632d?w=400",
      size: "small",
      origin: "광주광역시 북구",
      destination: "서울특별시 강남구",
      scheduled_date: "2026-04-10",
      current_volunteers: 2,
      needed_volunteers: 3,
    },
  },
];

// ── 더미 대화 (session-001 — 수락 후 매칭 확정) ──────────────────────────────

const DEMO_MESSAGES_1_ACCEPT: Message[] = [
  {
    role: "bot", type: "text",
    text: "수락 완료됐어요! 보호소 최종 확인 후 매칭이 확정돼요. 알림으로 알려드릴게요. 🐾",
  },
  {
    role: "bot", type: "matching_confirmed",
    info: {
      segment_id: 42,
      animal_name: "초코",
      photo_url: "https://images.unsplash.com/photo-1552053831-71594a27632d?w=400",
      size: "small",
      my_segment: { from: "광주광역시 북구", to: "천안역" },
      scheduled_date: "2026-04-10",
      depart_time: "09:00",
      estimated_arrival_time: "10:40",
      open_chat_url: "https://open.kakao.com/o/dummy",
      handover_candidates: [
        { name: "천안아산역", type: "station", distance_km: 0.3 },
        { name: "천안터미널", type: "terminal", distance_km: 1.2 },
        { name: "목천휴게소", type: "rest_area", distance_km: 8.5 },
      ],
      prev_volunteer: undefined,
      next_volunteer: "이릴레이",
    },
  },
  {
    role: "bot", type: "text",
    text: "인계 코드는 매칭 확정 페이지에서 출발 당일 00:00에 공개돼요. 확정 알림을 눌러 확인해 주세요!",
  },
  {
    role: "bot", type: "ping_check",
    segment_id: 42,
    animal_name: "초코",
    depart_time: "09:00",
    from: "광주광역시 북구",
  },
];

// ── 더미 대화 (session-002 전용 — 동선 등록 전체 흐름 + CONFIRM 버튼) ──────────

const DEMO_MESSAGES_2: Message[] = [
  {
    role: "bot", type: "text",
    text: "안녕하세요! 릴레이 도우미예요. 🐾\n봉사 일정을 자유롭게 말씀해 주세요. 출발 지역, 날짜, 차량 유무 등 편하게 입력하시면 돼요.",
  },
  {
    role: "user", type: "text",
    text: "광주에서 출발 가능하고, 4월 10일에 시간 돼",
  },
  {
    role: "bot", type: "text",
    text: "광주 출발, 4월 10일 확인했어요! 차량이 있으신가요? 없으시면 대중교통 이용도 괜찮아요.",
  },
  {
    role: "user", type: "text",
    text: "차량 있어. 소형 동물까지 가능해",
  },
  {
    role: "bot", type: "text",
    text: "알겠어요! 출발 예정 시간과 도착 예정 시간도 알려주세요.\n예) 09:00 출발 → 10:30 도착 예정",
  },
  { role: "user", type: "text", text: "9시에 출발해서 10시 반쯤 도착할 것 같아" },
  {
    role: "bot", type: "text",
    text: "감사합니다! 아래 내용으로 동선을 등록할까요?\n\n출발지: 광주광역시\n날짜: 2026-04-10\n차량: 있음\n최대 동물 크기: 소형 (5kg 이하)\n출발 시간: 09:00\n도착 예정: 10:30",
  },
];

// ── 봇 메시지 래퍼 ────────────────────────────────────────────────────────────

function BotRow({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex justify-start">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gray-100 mr-2 mt-0.5">
        <MessageCircle size={16} className="text-gray-300 fill-gray-300" />
      </div>
      <div className="max-w-[85%]">{children}</div>
    </div>
  );
}

// ── 공고 카드 말풍선 ──────────────────────────────────────────────────────────

function PostCardBubble({ post }: { post: PostSuggestion }) {
  return (
    <div className="w-[240px] rounded-2xl overflow-hidden bg-white border border-gray-100 shadow-sm">
      <div className="relative h-28 bg-gray-100">
        {post.photo_url
          ? <Image src={post.photo_url} alt={post.animal_name} fill className="object-cover" />
          : <div className="flex h-full items-center justify-center text-4xl">🐾</div>}
        <span className="absolute top-2 right-2 rounded-full bg-white/90 px-2 py-0.5 text-[10px] font-bold text-[#EEA968]">
          {SIZE_LABEL[post.max_animal_size]}
        </span>
      </div>
      <div className="px-3 py-2.5">
        <p className="text-[14px] font-bold text-gray-900 mb-1">{post.animal_name}</p>
        <div className="flex items-center gap-1 text-[12px] text-gray-500 mb-0.5">
          <MapPin size={10} className="text-[#EEA968] shrink-0" />
          <span className="truncate">{post.origin}</span>
          <ArrowRight size={9} className="text-gray-300 shrink-0" />
          <span className="truncate">{post.destination}</span>
        </div>
        <div className="flex items-center gap-1 text-[12px] text-gray-400">
          <Calendar size={10} className="text-[#EEA968] shrink-0" />
          <span>{post.scheduled_date}</span>
        </div>
      </div>
    </div>
  );
}

// ── 매칭 이유 ─────────────────────────────────────────────────────────────────

function MatchingReasonBubble({ reason, chain }: { reason: string; chain: ChainSegment[] }) {
  const waypoints = [chain[0].from, ...chain.map((s) => s.to)];
  const myIdx = chain.findIndex((s) => s.isMe);

  function shortName(place: string) {
    return place.replace(/특별시|광역시|특별자치시/, "").trim();
  }

  return (
    <div className="w-[260px] rounded-2xl bg-white border border-gray-100 shadow-sm overflow-hidden">
      <div className="bg-[#A07050] px-3 py-2 flex items-center gap-1.5">
        <PawPrint size={11} className="text-white/70" />
        <p className="text-[11px] font-bold text-white">AI 매칭 이유</p>
      </div>

      {/* 웨이포인트 체인 */}
      <div className="px-3 pt-3 pb-1 overflow-x-auto">
        <div className="flex items-start">
          {waypoints.map((wp, i) => {
            const isMine = myIdx !== -1 && i >= myIdx && i <= myIdx + 1;
            const isLastNode = i === waypoints.length - 1;
            return (
              <div key={i} className="flex items-start">
                <div className="flex flex-col items-center" style={{ minWidth: 44 }}>
                  <div className={`h-3 w-3 rounded-full border-2 ${isMine ? "bg-[#EEA968] border-[#EEA968]" : "bg-white border-gray-300"}`} />
                  <span className={`mt-1 text-[8px] text-center leading-tight break-words max-w-[44px] ${isMine ? "font-bold text-gray-800" : "text-gray-400"}`}>
                    {shortName(wp)}
                  </span>
                </div>
                {!isLastNode && (
                  <div className={`mt-[5px] h-0.5 w-4 flex-shrink-0 ${myIdx !== -1 && i === myIdx ? "bg-[#EEA968]" : "bg-gray-200"}`} />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* 봉사자 목록 */}
      <div className="px-3 pt-1.5 pb-2 space-y-0.5">
        {chain.map((seg, i) => (
          <div key={i} className="flex items-center gap-1.5">
            <div className={`flex-shrink-0 h-3.5 w-3.5 rounded-full flex items-center justify-center text-[8px] font-bold ${seg.isMe ? "bg-[#EEA968] text-white" : "bg-gray-100 text-gray-500"}`}>
              {i + 1}
            </div>
            <span className={`flex-1 text-[10px] truncate ${seg.isMe ? "font-semibold text-gray-800" : "text-gray-400"}`}>
              {seg.volunteer}
            </span>
            {seg.isMe && (
              <span className="text-[8px] font-bold text-[#EEA968] bg-gray-100 px-1 py-0.5 rounded-full shrink-0">참여 중</span>
            )}
          </div>
        ))}
      </div>

      <div className="px-3 pb-2.5">
        <div className="h-px bg-gray-50 mb-1.5" />
        <p className="text-[11px] text-gray-400 leading-relaxed">{reason}</p>
      </div>
    </div>
  );
}

// ── 봉사 추천 카드 (수락/거절) ────────────────────────────────────────────────

function RecommendationBubble({
  rec,
  onAccept,
  onReject,
  onViewDetail,
  decided,
}: {
  rec: RecommendedPost;
  onAccept: () => void;
  onReject: () => void;
  onViewDetail: () => void;
  decided?: boolean;
}) {
  const filledSlots = rec.current_volunteers;
  const totalSlots = rec.needed_volunteers;

  return (
    <div className="w-[240px] rounded-2xl bg-white border border-gray-100 shadow-sm overflow-hidden">
      {/* 이미지 + 동물명 가로 배치 */}
      <div className="flex items-center gap-2.5 px-3 pt-3 pb-2">
        <div className="relative h-12 w-12 rounded-xl overflow-hidden bg-gray-100 shrink-0">
          {rec.photo_url
            ? <Image src={rec.photo_url} alt={rec.animal_name} fill className="object-cover" />
            : <div className="flex h-full items-center justify-center text-xl">🐾</div>}
        </div>
        <div className="min-w-0">
          <div className="flex items-center gap-1.5 mb-0.5">
            <p className="text-[14px] font-bold text-gray-900 truncate">{rec.animal_name}</p>
            <span className="shrink-0 rounded-full bg-gray-100 px-1.5 py-0.5 text-[9px] font-bold text-gray-500">{SIZE_LABEL[rec.size]}</span>
          </div>
          <div className="flex items-center gap-1 text-[11px] text-gray-500">
            <MapPin size={9} className="text-[#EEA968] shrink-0" />
            <span className="truncate">{rec.origin}</span>
            <ArrowRight size={8} className="text-gray-300 shrink-0" />
            <span className="truncate">{rec.destination}</span>
          </div>
        </div>
      </div>

      <div className="px-3 pb-2">
        <div className="flex items-center justify-between text-[11px] text-gray-400 mb-1.5">
          <div className="flex items-center gap-1">
            <Calendar size={10} className="text-[#EEA968]" />
            <span>{rec.scheduled_date}</span>
          </div>
          <div className="flex items-center gap-1">
            <Users size={10} />
            <span>{filledSlots}/{totalSlots}명</span>
          </div>
        </div>
        {/* 슬롯 바 */}
        <div className="flex gap-0.5 mb-2.5">
          {Array.from({ length: totalSlots }).map((_, i) => (
            <div key={i} className={`h-1 flex-1 rounded-full ${i < filledSlots ? "bg-[#EEA968]" : "bg-gray-100"}`} />
          ))}
        </div>
      </div>

      <div className="px-3 pb-1">
        <button
          onClick={onViewDetail}
          className="w-full flex items-center justify-center gap-1 h-8 rounded-full bg-gray-50 text-[11px] font-semibold text-gray-500 active:scale-95 transition-transform"
        >
          <ExternalLink size={11} />
          상세 보기
        </button>
      </div>
      <div className="flex gap-1.5 px-3 pb-3">
        <button
          onClick={onAccept}
          disabled={decided}
          className="flex-1 h-9 rounded-full bg-[#EEA968] text-[12px] font-bold text-white active:scale-95 disabled:opacity-30 disabled:cursor-not-allowed"
        >
          수락
        </button>
        <button
          onClick={onReject}
          disabled={decided}
          className="flex-1 h-9 rounded-full border border-gray-200 text-[12px] font-semibold text-gray-400 active:scale-95 disabled:opacity-30 disabled:cursor-not-allowed"
        >
          거절
        </button>
      </div>
    </div>
  );
}

// ── 매칭 확정 카드 ────────────────────────────────────────────────────────────

function MatchingConfirmedBubble({ info, onViewDetail }: { info: MatchingInfo; onViewDetail: () => void }) {
  return (
    <div className="w-[260px] rounded-2xl bg-white border border-gray-100 shadow-sm overflow-hidden">
      {/* 헤더 */}
      <div className="bg-[#A07050] px-3 py-2 flex items-center gap-1.5">
        <CheckCircle2 size={13} className="text-white" />
        <p className="text-[12px] font-bold text-white">매칭 확정!</p>
      </div>

      {/* 동물 + 내 구간 한 줄 */}
      <div className="flex items-center gap-2.5 px-3 py-2.5 border-b border-gray-50">
        <div className="relative h-10 w-10 rounded-xl overflow-hidden bg-gray-100 shrink-0">
          {info.photo_url
            ? <Image src={info.photo_url} alt={info.animal_name} fill className="object-cover" />
            : <div className="flex h-full items-center justify-center text-lg">🐾</div>}
        </div>
        <div className="min-w-0">
          <p className="text-[13px] font-bold text-gray-900 truncate">{info.animal_name}</p>
          <p className="text-[10px] text-gray-400">{SIZE_LABEL[info.size]} · {info.scheduled_date}</p>
        </div>
      </div>

      <div className="px-3 py-2.5 space-y-2">
        {/* 내 구간 */}
        <div className="rounded-xl bg-gray-50 px-2.5 py-2">
          <p className="text-[9px] font-bold text-[#EEA968] mb-1">
            내 담당 구간 · {info.depart_time} 출발{info.estimated_arrival_time && ` → ${info.estimated_arrival_time} 도착 예정`}
          </p>
          <div className="flex items-center gap-1 text-[12px] font-semibold text-gray-800 flex-wrap">
            <span>{info.my_segment.from}</span>
            <ArrowRight size={9} className="text-[#EEA968] shrink-0" />
            <span>{info.my_segment.to}</span>
          </div>
        </div>

        {/* 인계 후보지 — 최대 2개만 */}
        <div>
          <p className="text-[10px] text-gray-400 mb-1">
            인계 후보지{info.next_volunteer && <span className="ml-1">· {info.next_volunteer}님과</span>}
          </p>
          <div className="space-y-0.5">
            {info.handover_candidates.slice(0, 2).map((c, i) => (
              <div key={i} className="flex items-center gap-1.5 text-[11px]">
                <span className={`h-3.5 w-3.5 rounded-full flex items-center justify-center text-[8px] font-bold shrink-0 ${i === 0 ? "bg-[#EEA968] text-white" : "bg-gray-100 text-gray-400"}`}>
                  {i + 1}
                </span>
                <span className="font-medium text-gray-700 truncate">{c.name}</span>
                <span className="ml-auto text-gray-400 shrink-0">{c.distance_km}km</span>
              </div>
            ))}
          </div>
        </div>

        {/* 오픈채팅 */}
        <a
          href={info.open_chat_url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-between h-9 rounded-xl bg-gray-100 px-3 active:scale-[0.97] transition-transform"
        >
          <span className="text-[12px] font-bold text-gray-500">카카오 오픈채팅 참여</span>
          <ExternalLink size={12} className="text-gray-400" />
        </a>
        <button
          onClick={onViewDetail}
          className="w-full flex items-center justify-center gap-1 h-9 rounded-xl border border-gray-200 text-[12px] font-semibold text-gray-500 active:scale-[0.97] transition-transform"
        >
          <ExternalLink size={11} />
          매칭 상세 보기
        </button>
      </div>
    </div>
  );
}


// ── 핑 체크 버블 ──────────────────────────────────────────────────────────────

function PingCheckBubble({
  animalName,
  departTime,
  from,
  onConfirm,
  onDelay,
  answered,
}: {
  animalName: string;
  departTime: string;
  from: string;
  onConfirm: () => void;
  onDelay: () => void;
  answered: boolean;
}) {
  return (
    <div className="w-[260px] rounded-2xl bg-white border border-gray-100 shadow-sm overflow-hidden">
      <div className="bg-orange-50 px-4 py-2.5 flex items-center gap-2">
        <div className="h-2 w-2 rounded-full bg-orange-400 animate-pulse shrink-0" />
        <p className="text-[12px] font-bold text-orange-500">출발 확인 요청</p>
      </div>
      <div className="px-4 py-3.5 space-y-3">
        <div className="space-y-1">
          <p className="text-[13px] font-semibold text-gray-800">
            [{animalName}] 출발 2시간 전이에요!
          </p>
          <p className="text-[12px] text-gray-500 leading-relaxed">
            {from} → {departTime} 출발<br />
            정상 출발하실 수 있나요?
          </p>
        </div>
        {answered ? (
          <div className="flex items-center gap-1.5 rounded-xl bg-green-50 px-3 py-2">
            <CheckCircle2 size={13} className="text-green-500 shrink-0" />
            <p className="text-[12px] font-semibold text-green-600">출발 확인 완료</p>
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            <button
              onClick={onConfirm}
              className="w-full h-10 rounded-xl bg-[#EEA968] text-[13px] font-bold text-white active:scale-[0.98] transition-transform"
            >
              네, 출발할게요!
            </button>
            <button
              onClick={onDelay}
              className="w-full h-10 rounded-xl bg-gray-100 text-[13px] font-semibold text-gray-600 active:scale-[0.98] transition-transform"
            >
              지연될 것 같아요
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// ── 알림 버블 (실제 백엔드 notifications 기반) ────────────────────────────────

const NOTIF_CONFIG: Record<string, { label: string; headerClass: string; icon: React.ReactNode; btnLabel: string }> = {
  matching_proposed: {
    label: "새 매칭 제안",
    headerClass: "bg-[#EEA968]",
    icon: <PawPrint size={11} className="text-white/80" />,
    btnLabel: "매칭 제안 보기",
  },
  matching_confirmed: {
    label: "매칭 확정!",
    headerClass: "bg-[#A07050]",
    icon: <CheckCircle2 size={12} className="text-white" />,
    btnLabel: "매칭 상세 보기",
  },
  ping_check: {
    label: "출발 확인 요청",
    headerClass: "bg-orange-400",
    icon: <div className="h-2 w-2 rounded-full bg-white animate-pulse" />,
    btnLabel: "매칭 상세 보기",
  },
};

function NotificationBubble({
  notifType,
  message,
  url,
  onNavigate,
}: {
  notifType: string;
  message: string;
  url?: string;
  onNavigate: () => void;
}) {
  const cfg = NOTIF_CONFIG[notifType] ?? {
    label: "알림",
    headerClass: "bg-gray-400",
    icon: null,
    btnLabel: "보러 가기",
  };

  return (
    <div className="w-[260px] rounded-2xl bg-white border border-gray-100 shadow-sm overflow-hidden">
      <div className={`${cfg.headerClass} px-3 py-2 flex items-center gap-1.5`}>
        {cfg.icon}
        <p className="text-[11px] font-bold text-white">{cfg.label}</p>
      </div>
      <div className="px-3 py-2.5 space-y-2.5">
        <p className="text-[12px] text-gray-600 leading-relaxed">{message}</p>
        {url && (
          <button
            onClick={onNavigate}
            className="w-full flex items-center justify-center gap-1 h-9 rounded-xl border border-gray-200 text-[12px] font-semibold text-gray-500 active:scale-[0.97] transition-transform"
          >
            <ExternalLink size={11} />
            {cfg.btnLabel}
          </button>
        )}
      </div>
    </div>
  );
}

// ── 공고 요약 카드 (Sticky) ────────────────────────────────────────────────────

interface RegisteredFields { origin?: string; vehicle?: string; available_time?: string; estimated_arrival_time?: string; }

function PostSummaryCard({ postContext, registered }: { postContext: PostContext; registered?: RegisteredFields }) {
  const fields = [
    { label: "출발지", value: registered?.origin },
    { label: "도착지", value: postContext.destination },
    { label: "날짜",   value: postContext.available_date },
    { label: "차량",   value: registered?.vehicle },
    { label: "크기",   value: postContext.max_animal_size ? SIZE_LABEL[postContext.max_animal_size] : undefined },
    { label: "출발",   value: registered?.available_time },
    { label: "도착예정", value: registered?.estimated_arrival_time },
  ];

  return (
    <div className="sticky top-[65px] z-10 bg-white border-b border-gray-100">
      <div className="mx-auto max-w-2xl px-4 py-3">
      <div className="flex gap-2 overflow-x-auto pb-0.5">
        {fields.map(({ label, value }) => (
          <div
            key={label}
            className={`flex-shrink-0 flex flex-col gap-1 rounded-xl px-3 py-2 border ${
              value
                ? "bg-gray-50 border-gray-100"
                : "bg-white border-dashed border-gray-200"
            }`}
          >
            <span className="text-[9px] text-gray-400 leading-none">{label}</span>
            <span className={`text-[11px] font-semibold leading-none ${value ? "text-gray-700" : "text-gray-300"}`}>
              {value ?? "미정"}
            </span>
          </div>
        ))}
      </div>
      </div>
    </div>
  );
}

// ── 페이지 ────────────────────────────────────────────────────────────────────

export default function ChatRoomPage() {
  const router = useRouter();
  const params = useParams();
  const sessionId = params.session_id as string;
  const isDemo = sessionId === "session-001";
  const isDemo2 = sessionId === "session-002";

  const [messages, setMessages] = useState<Message[]>([]);
  const [beSessionId, setBeSessionId] = useState<string | null>(null);
  const [postContext, setPostContext] = useState<PostContext | null>(null);
  const [completed, setCompleted] = useState(false);
  const [initializing, setInitializing] = useState(true);
  const [sending, setSending] = useState(false);
  const [textInput, setTextInput] = useState("");
  const [confirmOptions, setConfirmOptions] = useState<string[] | null>(null);
  const [registeredFields, setRegisteredFields] = useState<RegisteredFields | undefined>(undefined);
  const [matchingDecided, setMatchingDecided] = useState(false);
  const [pingAnswered, setPingAnswered] = useState(false);

  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  function notifsToMessages(notifs: AppNotification[]): Message[] {
    return notifs
      .filter((n) => ["matching_proposed", "matching_confirmed", "ping_check"].includes(n.type))
      .map((n) => ({
        role: "bot" as const,
        type: "notification" as const,
        notif_id: n.id,
        notif_type: n.type,
        message: n.message,
        segment_id: n.payload.segment_id,
        url: n.payload.url,
      }));
  }

  async function appendUnreadNotifications() {
    try {
      const notifs = await getUnreadNotifications();
      const msgs = notifsToMessages(notifs);
      if (msgs.length > 0) {
        setMessages((prev) => [...prev, ...msgs]);
        notifs.forEach((n) => markNotificationRead(n.id).catch((err) => {
          console.error(`알림 읽음 처리 실패 (id: ${n.id})`, err);
        }));
      }
    } catch {}
  }

  const DEMO_CACHE_KEY = `demoChat_${sessionId}`;

  function saveDemoState() {
    if (!(isDemo || isDemo2) || messages.length === 0) return;
    sessionStorage.setItem(DEMO_CACHE_KEY, JSON.stringify({
      messages, matchingDecided, pingAnswered, registeredFields, confirmOptions,
    }));
  }

  useEffect(() => {
    const raw = sessionStorage.getItem(CHATBOT_POST_CONTEXT_KEY);
    const context: PostContext | null = raw ? JSON.parse(raw) : null;
    setPostContext(context);

    // 캐시된 상태 복원 (매칭 상세 다녀온 경우)
    const raw2 = sessionStorage.getItem(DEMO_CACHE_KEY);
    if (raw2 && (isDemo || isDemo2)) {
      const s = JSON.parse(raw2);
      setMessages(s.messages ?? []);
      setMatchingDecided(s.matchingDecided ?? false);
      setPingAnswered(s.pingAnswered ?? false);
      setRegisteredFields(s.registeredFields);
      setConfirmOptions(s.confirmOptions ?? null);
      setInitializing(false);
      // StrictMode 이중 마운트 대응: 즉시 삭제 대신 지연 삭제
      setTimeout(() => sessionStorage.removeItem(DEMO_CACHE_KEY), 100);
      // 수락/거절 결과 처리
      const action = sessionStorage.getItem("matchingAction");
      if (action) {
        sessionStorage.removeItem("matchingAction");
        setTimeout(() => {
          if (action === "accepted") {
            setMatchingDecided(true);
            showSequential(DEMO_MESSAGES_1_ACCEPT, 500);
          } else if (action === "declined") {
            setMatchingDecided(true);
            setCompleted(true);
            setMessages((prev) => [...prev, { role: "bot", type: "text", text: "알겠어요. 다른 기회에 또 연락드릴게요! 🐾" }]);
          }
        }, 600);
      }
      return;
    }

    if (isDemo) {
      // PRE 메시지 순차 표시 후 CONFIRM 버튼
      setInitializing(false);
      setMessages([]);
      setConfirmOptions(null);
      setRegisteredFields(undefined);
      const timers: ReturnType<typeof setTimeout>[] = [];
      DEMO_MESSAGES_1_PRE.forEach((msg, idx) => {
        const t = setTimeout(() => {
          setMessages((prev) => [...prev, msg]);
        }, idx * 400);
        timers.push(t);
      });
      const confirmTimer = setTimeout(() => {
        setConfirmOptions(["등록하기", "처음부터 다시"]);
      }, DEMO_MESSAGES_1_PRE.length * 400);
      timers.push(confirmTimer);
      return () => {
        timers.forEach(clearTimeout);
        setMessages([]);
        setConfirmOptions(null);
      };
    }

    if (isDemo2) {
      // 동선 등록 흐름 데모: CONFIRM 버튼까지 순차 표시
      setInitializing(false);
      setMessages([]);
      setConfirmOptions(null);
      const timers: ReturnType<typeof setTimeout>[] = [];
      DEMO_MESSAGES_2.forEach((msg, idx) => {
        const t = setTimeout(() => {
          setMessages((prev) => [...prev, msg]);
        }, idx * 600);
        timers.push(t);
      });
      // 마지막 메시지 이후 CONFIRM 버튼 표시
      const confirmTimer = setTimeout(() => {
        setConfirmOptions(["등록하기", "처음부터 다시"]);
      }, DEMO_MESSAGES_2.length * 600);
      timers.push(confirmTimer);
      return () => {
        timers.forEach(clearTimeout);
        setMessages([]);
        setConfirmOptions(null);
      };
    }

    initConversation(context);
  }, [isDemo, isDemo2]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  // Service Worker postMessage → 푸시 수신 시 버블 추가
  useEffect(() => {
    if (isDemo || isDemo2) return;
    function handleSwMessage(e: MessageEvent) {
      if (e.data?.type !== "PUSH_NOTIFICATION") return;
      const { payload } = e.data;
      setMessages((prev) => [
        ...prev,
        {
          role: "bot" as const,
          type: "notification" as const,
          notif_id: Date.now(),
          notif_type: payload.type ?? "",
          message: payload.message ?? "",
          segment_id: payload.segment_id,
          url: payload.url,
        },
      ]);
    }
    navigator.serviceWorker?.addEventListener("message", handleSwMessage);
    return () => navigator.serviceWorker?.removeEventListener("message", handleSwMessage);
  }, [isDemo, isDemo2]);

  // 마지막 메시지를 localStorage에 저장 (채팅 목록에서 미리보기용)
  useEffect(() => {
    if (messages.length === 0) return;
    const last = messages[messages.length - 1];
    let preview = "";
    if (last.type === "text") preview = last.text.replace(/\n/g, " ");
    else if (last.type === "recommendation") preview = `[${last.rec.animal_name}] 매칭 제안이 도착했어요`;
    else if (last.type === "matching_confirmed") preview = `[${last.info.animal_name}] 매칭이 확정됐어요!`;
    else if (last.type === "ping_check") preview = `[${last.animal_name}] 출발 확인 요청이 왔어요`;
    else if (last.type === "notification") preview = last.message;
    else if (last.type === "matching_reason") preview = "AI 매칭 이유가 도착했어요";
    else if (last.type === "post_card") preview = "공고 정보가 도착했어요";
    if (preview) localStorage.setItem(`chatLastMsg_${sessionId}`, preview);
  }, [messages, sessionId]);


  async function initConversation(context: PostContext | null) {
    setInitializing(true);
    try {
      // 채팅 목록에서 새 세션 시작 시 이미 초기화된 응답이 있으면 재사용
      const cached = sessionStorage.getItem(`chatbot_init_${sessionId}`);
      if (cached) {
        sessionStorage.removeItem(`chatbot_init_${sessionId}`);
        const res = JSON.parse(cached);
        setBeSessionId(res.session_id);
        setMessages([{ role: "bot", type: "text", text: res.message }]);
        setConfirmOptions(res.options);
        if (!res.input_type) setTimeout(() => textareaRef.current?.focus(), 100);
        await appendUnreadNotifications();
        return;
      }
      const res = await sendChatMessage(null, context?.post_id ?? null, null);
      setBeSessionId(res.session_id);
      setMessages([{ role: "bot", type: "text", text: res.message }]);
      setConfirmOptions(res.options);
      if (!res.input_type) setTimeout(() => textareaRef.current?.focus(), 100);
      await appendUnreadNotifications();
    } catch {
      setMessages([{ role: "bot", type: "text", text: "채팅을 시작할 수 없습니다. 다시 시도해 주세요." }]);
    } finally {
      setInitializing(false);
    }
  }

  function showSequential(msgs: Message[], delayMs = 500) {
    msgs.forEach((msg, idx) => {
      setTimeout(() => setMessages((prev) => [...prev, msg]), (idx + 1) * delayMs);
    });
  }

  async function handleUserInput(userText: string) {
    if (sending) return;
    setMessages((prev) => [...prev, { role: "user", type: "text", text: userText }]);
    setConfirmOptions(null);
    setSending(true);

    // ── isDemo 특수 처리 ──────────────────────────────────────────────────────
    if (isDemo) {
      await new Promise((r) => setTimeout(r, 400));
      setSending(false);

      if (userText === "등록하기") {
        setRegisteredFields({ origin: "광주광역시", vehicle: "있음", available_time: "09:00", estimated_arrival_time: "10:40" });
        showSequential(DEMO_MESSAGES_1_POST, 600);
        return;
      }
      if (userText === "처음부터 다시") {
        setRegisteredFields(undefined);
        setConfirmOptions(null);
        setMessages([]);
        const timers: ReturnType<typeof setTimeout>[] = [];
        DEMO_MESSAGES_1_PRE.forEach((msg, idx) => {
          timers.push(setTimeout(() => setMessages((prev) => [...prev, msg]), idx * 400));
        });
        timers.push(setTimeout(() => setConfirmOptions(["등록하기", "처음부터 다시"]), DEMO_MESSAGES_1_PRE.length * 400));
        return;
      }
      if (userText === "수락할게요") {
        setMatchingDecided(true);
        showSequential(DEMO_MESSAGES_1_ACCEPT, 500);
        return;
      }
      if (userText === "거절할게요") {
        setMatchingDecided(true);
        setCompleted(true);
        setMessages((prev) => [...prev, { role: "bot", type: "text", text: "알겠어요. 다른 기회에 또 연락드릴게요! 🐾" }]);
        return;
      }
      return;
    }

    // ── isDemo2 특수 처리 ─────────────────────────────────────────────────────
    if (isDemo2) {
      await new Promise((r) => setTimeout(r, 400));
      setSending(false);

      if (userText === "등록하기") {
        setRegisteredFields({ origin: "광주광역시", vehicle: "있음", available_time: "09:00", estimated_arrival_time: "10:30" });
        setCompleted(true);
        setConfirmOptions(null);
        setTimeout(() => setMessages((prev) => [...prev, { role: "bot", type: "text", text: "봉사 정보가 등록되었어요! 매칭 제안 해드릴게요. 🐾" }]), 400);
        return;
      }
      if (userText === "처음부터 다시") {
        setRegisteredFields(undefined);
        setConfirmOptions(null);
        setMessages([]);
        const timers: ReturnType<typeof setTimeout>[] = [];
        DEMO_MESSAGES_2.forEach((msg, idx) => {
          timers.push(setTimeout(() => setMessages((prev) => [...prev, msg]), idx * 600));
        });
        timers.push(setTimeout(() => setConfirmOptions(["등록하기", "처음부터 다시"]), DEMO_MESSAGES_2.length * 600));
        return;
      }
      return;
    }

    // ── 실제 API ──────────────────────────────────────────────────────────────
    try {
      const res = await sendChatMessage(beSessionId, null, userText);
      setMessages((prev) => [...prev, { role: "bot", type: "text", text: res.message }]);
      setConfirmOptions(res.options);
      if (res.completed) {
        setCompleted(true);
        setConfirmOptions(null);
        sessionStorage.removeItem(CHATBOT_SESSION_KEY);
        sessionStorage.removeItem(CHATBOT_POST_CONTEXT_KEY);
      } else if (!res.input_type) {
        setTimeout(() => textareaRef.current?.focus(), 100);
      }
    } catch {
      setMessages((prev) => [...prev, { role: "bot", type: "text", text: "오류가 발생했어요. 다시 시도해 주세요." }]);
    } finally {
      setSending(false);
    }
  }

  if (initializing) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-white">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-[#EEA968] border-t-transparent" />
      </main>
    );
  }

  return (
    <main className="flex min-h-screen flex-col bg-gray-50">

      {/* 헤더 */}
      <header className="sticky top-0 z-20 bg-white border-b border-gray-100">
        <div className="mx-auto max-w-2xl flex items-center gap-3 px-4 py-4">
          <button onClick={() => router.back()} className="flex h-9 w-9 items-center justify-center rounded-xl text-gray-500 hover:bg-gray-100 transition-colors" aria-label="뒤로 가기">
            <ArrowLeft size={20} />
          </button>
          <div>
            <p className="text-[16px] font-bold text-gray-800 leading-tight">
              {postContext?.animal_name ? `[${postContext.animal_name}] 릴레이 지원` : "릴레이 도우미"}
            </p>
            <p className="text-[11px] text-gray-400">무엇이든 물어보세요</p>
          </div>
        </div>
      </header>

      {/* 공고 요약 카드 */}
      {postContext && <PostSummaryCard postContext={postContext} registered={registeredFields} />}

      {/* 메시지 목록 */}
      <div className="flex-1 overflow-y-auto pb-36">
      <div className="mx-auto max-w-2xl px-4 py-4 flex flex-col gap-3">
        {messages.map((msg, i) => {
          if (msg.type === "notification") return (
            <BotRow key={i}>
              <NotificationBubble
                notifType={msg.notif_type}
                message={msg.message}
                url={msg.url}
                onNavigate={() => {
                  if (msg.url) {
                    sessionStorage.setItem("matchingChatSession", sessionId);
                    router.push(msg.url);
                  }
                }}
              />
            </BotRow>
          );
          if (msg.type === "post_card") return (
            <BotRow key={i}><PostCardBubble post={msg.post} /></BotRow>
          );
          if (msg.type === "matching_reason") return (
            <BotRow key={i}><MatchingReasonBubble reason={msg.reason} chain={msg.chain} /></BotRow>
          );
          if (msg.type === "recommendation") return (
            <BotRow key={i}>
              <RecommendationBubble
                rec={msg.rec}
                onAccept={() => handleUserInput("수락할게요")}
                onReject={() => handleUserInput("거절할게요")}
                onViewDetail={() => {
                  saveDemoState();
                  sessionStorage.setItem("matchingChatSession", sessionId);
                  router.push(`/volunteer/matching/${msg.rec.segment_id}`);
                }}
                decided={matchingDecided}
              />
            </BotRow>
          );
          if (msg.type === "matching_confirmed") return (
            <BotRow key={i}>
              <MatchingConfirmedBubble
                info={msg.info}
                onViewDetail={() => {
                  saveDemoState();
                  sessionStorage.setItem("matchingChatSession", sessionId);
                  router.push(`/volunteer/matching/${msg.info.segment_id}`);
                }}
              />
            </BotRow>
          );
          if (msg.type === "ping_check") return (
            <BotRow key={i}>
              <PingCheckBubble
                animalName={msg.animal_name}
                departTime={msg.depart_time}
                from={msg.from}
                answered={pingAnswered}
                onConfirm={() => {
                  setPingAnswered(true);
                  setMessages((prev) => [...prev,
                    { role: "bot", type: "text", text: "출발 확인 완료! 안전하게 출발하세요. 🐾\n이동 중 체크포인트를 눌러 진행 상황을 기록해 주세요." },
                  ]);
                }}
                onDelay={() => {
                  setPingAnswered(true);
                  setMessages((prev) => [...prev,
                    { role: "bot", type: "text", text: "알겠어요. 지연 사유를 입력해 주시면 보호소와 다음 봉사자에게 안내해 드릴게요." },
                  ]);
                }}
              />
            </BotRow>
          );
          // text
          return (
            <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              {msg.role === "bot" && (
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gray-100 mr-2 mt-0.5">
                  <MessageCircle size={16} className="text-gray-300 fill-gray-300" />
                </div>
              )}
              <div className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-[14px] leading-relaxed whitespace-pre-wrap ${
                msg.role === "bot"
                  ? "bg-white text-gray-800 shadow-sm border border-gray-100 rounded-tl-sm"
                  : "bg-[#EEA968] text-white rounded-tr-sm"
              }`}>
                {msg.text}
              </div>
            </div>
          );
        })}

        {sending && (
          <div className="flex justify-start">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gray-100 mr-2">
              <MessageCircle size={16} className="text-gray-300 fill-gray-300" />
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
      </div>

      {/* 하단 입력 영역 */}
      <div className="fixed bottom-16 left-0 right-0 z-20 bg-white border-t border-gray-100">
        <div className="mx-auto max-w-2xl px-4 py-3">
          {confirmOptions ? (
            /* CONFIRM 버튼 */
            <div className="flex gap-2">
              {confirmOptions.map((opt) => (
                <button
                  key={opt}
                  onClick={() => { handleUserInput(opt); setTextInput(""); }}
                  disabled={sending}
                  className={`flex-1 h-12 rounded-full text-[14px] font-bold transition-colors active:scale-[0.97] disabled:opacity-40 ${
                    opt === "등록하기"
                      ? "bg-[#EEA968] text-white shadow-md shadow-[#EEA968]/20"
                      : "border border-gray-200 text-gray-500 bg-white"
                  }`}
                >
                  {opt}
                </button>
              ))}
            </div>
          ) : (
            /* 자유 입력 textarea */
            <div className="flex items-end gap-2 bg-gray-50 rounded-2xl px-3 py-2">
              <textarea
                ref={textareaRef}
                value={textInput}
                onChange={(e) => {
                  setTextInput(e.target.value);
                  e.target.style.height = "auto";
                  e.target.style.height = `${Math.min(e.target.scrollHeight, 120)}px`;
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
                    e.preventDefault();
                    const text = textInput.trim();
                    if (text) { handleUserInput(text); setTextInput(""); }
                  }
                }}
                placeholder="자유롭게 입력해 주세요"
                rows={1}
                disabled={sending}
                className="flex-1 resize-none bg-transparent text-[14px] text-gray-800 placeholder:text-gray-400 focus:outline-none leading-relaxed overflow-hidden disabled:opacity-50 py-1"
              />
              <button
                onClick={() => {
                  const text = textInput.trim();
                  if (text) { handleUserInput(text); setTextInput(""); }
                }}
                disabled={!textInput.trim() || sending}
                className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#EEA968] text-white disabled:opacity-30 active:scale-95 transition-all mb-0.5"
              >
                <ArrowUp size={16} strokeWidth={2.5} />
              </button>
            </div>
          )}
        </div>
      </div>

    </main>
  );
}
