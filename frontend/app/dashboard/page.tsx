"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { User, Plus, X, ChevronRight, Users, ArrowRight } from "lucide-react";

// ── Types ──────────────────────────────────────────────────────────────────────

type PostStatus = "urgent" | "recruiting" | "waiting" | "in_progress" | "completed";
type TabKey = "all" | "urgent" | "recruiting" | "waiting" | "completed";

interface Volunteer {
  id: number;
  name: string;
  from: string;
  to: string;
}

interface RelaySegment {
  volunteer: string;
  from: string;
  to: string;
  time: string;
}

interface Post {
  id: number;
  animal: { name: string; size: "소형" | "중형" | "대형"; species: string };
  origin: string;
  destination: string;
  scheduledDate: string;
  status: PostStatus;
  volunteers: Volunteer[];
  relayChain?: RelaySegment[];
  matchingReason?: string;
}

// ── Dummy Data ─────────────────────────────────────────────────────────────────

const INITIAL_POSTS: Post[] = [
  {
    id: 1,
    animal: { name: "초코", size: "소형", species: "강아지" },
    origin: "광주광역시 북구",
    destination: "서울특별시 강남구",
    scheduledDate: "2026-04-10",
    status: "waiting",
    volunteers: [
      { id: 1, name: "김봉사", from: "광주역", to: "천안역" },
      { id: 2, name: "이릴레이", from: "천안역", to: "수원역" },
      { id: 3, name: "박도움", from: "수원역", to: "서울 강남구" },
    ],
    relayChain: [
      { volunteer: "김봉사", from: "광주역", to: "천안역", time: "09:00" },
      { volunteer: "이릴레이", from: "천안역", to: "수원역", time: "11:30" },
      { volunteer: "박도움", from: "수원역", to: "서울 강남구", time: "13:00" },
    ],
    matchingReason:
      "세 분의 이동 경로가 완벽하게 연결되며, 인계 시간 간격이 모두 30분 이상 확보됩니다.",
  },
  {
    id: 2,
    animal: { name: "뽀삐", size: "중형", species: "강아지" },
    origin: "부산광역시 해운대구",
    destination: "대구광역시 수성구",
    scheduledDate: "2026-04-12",
    status: "recruiting",
    volunteers: [
      { id: 4, name: "최자원", from: "부산역", to: "밀양역" },
      { id: 5, name: "정봉사", from: "밀양역", to: "경산역" },
    ],
  },
  {
    id: 3,
    animal: { name: "나비", size: "소형", species: "고양이" },
    origin: "인천광역시 남동구",
    destination: "경기도 수원시",
    scheduledDate: "2026-04-08",
    status: "urgent",
    volunteers: [
      { id: 6, name: "홍길동", from: "인천터미널", to: "수원역" },
    ],
  },
  {
    id: 4,
    animal: { name: "까미", size: "대형", species: "강아지" },
    origin: "대전광역시 유성구",
    destination: "서울특별시 송파구",
    scheduledDate: "2026-03-28",
    status: "completed",
    volunteers: [
      { id: 7, name: "신봉사", from: "대전역", to: "천안아산역" },
      { id: 8, name: "오릴레이", from: "천안아산역", to: "서울 송파구" },
    ],
  },
  {
    id: 5,
    animal: { name: "흰둥이", size: "소형", species: "강아지" },
    origin: "광주광역시 동구",
    destination: "경기도 성남시",
    scheduledDate: "2026-04-15",
    status: "waiting",
    volunteers: [
      { id: 9, name: "강자원", from: "광주송정역", to: "오송역" },
      { id: 10, name: "배봉사", from: "오송역", to: "경기 성남" },
    ],
    relayChain: [
      { volunteer: "강자원", from: "광주송정역", to: "오송역", time: "10:00" },
      { volunteer: "배봉사", from: "오송역", to: "경기 성남", time: "12:00" },
    ],
    matchingReason:
      "두 봉사자의 경로가 오송역에서 연결되며, 이동 시간과 인계 여유 시간이 최적화되어 있습니다.",
  },
  {
    id: 6,
    animal: { name: "루시", size: "중형", species: "강아지" },
    origin: "대구광역시 달서구",
    destination: "충청북도 청주시",
    scheduledDate: "2026-04-20",
    status: "recruiting",
    volunteers: [
      { id: 11, name: "임자원", from: "대구역", to: "김천구미역" },
      { id: 12, name: "한봉사", from: "김천구미역", to: "오송역" },
      { id: 13, name: "조릴레이", from: "오송역", to: "청주" },
    ],
  },
];

// ── Sub-components ─────────────────────────────────────────────────────────────

const TABS: { key: TabKey; label: string }[] = [
  { key: "all", label: "전체" },
  { key: "urgent", label: "🚨 긴급" },
  { key: "recruiting", label: "🟢 모집중" },
  { key: "waiting", label: "🟡 대기중" },
  { key: "completed", label: "⚪️ 봉사종료" },
];

function statusBadge(status: PostStatus) {
  const map: Record<PostStatus, { label: string; className: string }> = {
    urgent:      { label: "긴급",    className: "bg-red-100 text-red-600" },
    recruiting:  { label: "모집중",  className: "bg-green-100 text-green-700" },
    waiting:     { label: "대기중",  className: "bg-yellow-100 text-yellow-700" },
    in_progress: { label: "봉사중",  className: "bg-blue-100 text-blue-700" },
    completed:   { label: "봉사종료", className: "bg-gray-100 text-gray-500" },
  };
  const { label, className } = map[status];
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${className}`}>
      {label}
    </span>
  );
}

function sizeBadge(size: string) {
  const map: Record<string, string> = {
    소형: "bg-sky-50 text-sky-600",
    중형: "bg-indigo-50 text-indigo-600",
    대형: "bg-purple-50 text-purple-600",
  };
  return (
    <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${map[size] ?? ""}`}>
      {size}
    </span>
  );
}

// ── Bottom Sheet ───────────────────────────────────────────────────────────────

function BottomSheet({
  open,
  onClose,
  children,
}: {
  open: boolean;
  onClose: () => void;
  children: React.ReactNode;
}) {
  useEffect(() => {
    if (open) document.body.style.overflow = "hidden";
    else document.body.style.overflow = "";
    return () => { document.body.style.overflow = ""; };
  }, [open]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center">
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-[2px] animate-fade-in"
        onClick={onClose}
      />
      <div className="relative z-10 w-full max-w-lg rounded-t-3xl bg-white shadow-2xl animate-slide-up max-h-[85vh] flex flex-col">
        {/* 핸들 */}
        <div className="flex justify-center pt-3 pb-1 shrink-0">
          <div className="h-1 w-10 rounded-full bg-gray-200" />
        </div>
        <div className="overflow-y-auto flex-1 px-5 pb-8">{children}</div>
      </div>
    </div>
  );
}

// ── Toast ──────────────────────────────────────────────────────────────────────

function Toast({ message }: { message: string }) {
  if (!message) return null;
  return (
    <div className="fixed inset-x-0 top-5 z-[60] flex justify-center px-4 animate-fade-in">
      <div className="flex items-center gap-2.5 rounded-2xl bg-gray-900 px-5 py-3.5 shadow-xl">
        <svg className="shrink-0 text-green-400" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
          <polyline points="20 6 9 17 4 12" />
        </svg>
        <span className="text-[13px] font-semibold text-white">{message}</span>
      </div>
    </div>
  );
}

// ── Post Card ──────────────────────────────────────────────────────────────────

function PostCard({
  post,
  onShowApplicants,
  onShowMatching,
}: {
  post: Post;
  onShowApplicants: (post: Post) => void;
  onShowMatching: (post: Post) => void;
}) {
  const isUrgent = post.status === "urgent";
  const isWaiting = post.status === "waiting";
  const isRecruiting = post.status === "recruiting";

  return (
    <div
      className={`rounded-2xl bg-white border p-5 transition-shadow hover:shadow-md ${
        isUrgent ? "border-red-200 ring-1 ring-red-100" :
        isWaiting ? "border-yellow-200 ring-1 ring-yellow-100" :
        "border-gray-100"
      }`}
    >
      {/* 상단 행 */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2 flex-wrap">
          {statusBadge(post.status)}
          {sizeBadge(post.animal.size)}
          <span className="text-[12px] text-gray-400">{post.animal.species}</span>
        </div>
        <span className="text-[12px] text-gray-400 shrink-0">{post.scheduledDate}</span>
      </div>

      {/* 동물 이름 + 경로 */}
      <p className="text-[16px] font-bold text-gray-900 mb-1">
        {post.animal.name}
      </p>
      <div className="flex items-center gap-1.5 text-[13px] text-gray-500 mb-4">
        <span>{post.origin}</span>
        <ArrowRight size={13} className="text-gray-300 shrink-0" />
        <span>{post.destination}</span>
      </div>

      {/* 지원자 수 */}
      <div className="flex items-center gap-1.5 text-[13px] text-gray-500 mb-4">
        <Users size={14} className="text-gray-400" />
        <span>현재 지원: <span className="font-semibold text-gray-700">{post.volunteers.length}명</span></span>
      </div>

      {/* 액션 영역 */}
      {isWaiting && (
        <button
          onClick={() => onShowMatching(post)}
          className="w-full rounded-xl bg-yellow-400 py-3 text-[14px] font-bold text-gray-900 transition-all active:scale-[0.98] hover:bg-yellow-300 shadow-sm"
        >
          🔥 LLM 최적 매칭 결과 확인
        </button>
      )}

      {(isRecruiting || isUrgent) && (
        <button
          onClick={() => onShowApplicants(post)}
          className="w-full flex items-center justify-center gap-1.5 rounded-xl border border-gray-200 py-2.5 text-[13px] font-medium text-gray-600 transition-colors hover:bg-gray-50"
        >
          <Users size={14} />
          지원자 목록 확인
          <ChevronRight size={14} className="text-gray-400" />
        </button>
      )}
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────────────

export default function DashboardPage() {
  const [posts, setPosts] = useState<Post[]>(INITIAL_POSTS);
  const [activeTab, setActiveTab] = useState<TabKey>("all");
  const [selectedPost, setSelectedPost] = useState<Post | null>(null);
  const [sheetType, setSheetType] = useState<"applicants" | "matching" | null>(null);
  const [toast, setToast] = useState("");

  function showToast(msg: string) {
    setToast(msg);
    setTimeout(() => setToast(""), 4000);
  }

  function closeSheet() {
    setSelectedPost(null);
    setSheetType(null);
  }

  function handleShowApplicants(post: Post) {
    setSelectedPost(post);
    setSheetType("applicants");
  }

  function handleShowMatching(post: Post) {
    setSelectedPost(post);
    setSheetType("matching");
  }

  function handleApprove() {
    if (!selectedPost) return;
    setPosts((prev) =>
      prev.map((p) =>
        p.id === selectedPost.id ? { ...p, status: "in_progress" } : p
      )
    );
    closeSheet();
    showToast("릴레이 매칭이 확정되었습니다! 모든 봉사자에게 안내 이메일이 발송됩니다.");
  }

  function handleReject() {
    closeSheet();
    showToast("재매칭 요청이 접수되었습니다. 다음 배치 시 재처리됩니다.");
  }

  const filtered = posts.filter((p) => {
    if (activeTab === "all") return true;
    if (activeTab === "urgent") return p.status === "urgent";
    if (activeTab === "recruiting") return p.status === "recruiting";
    if (activeTab === "waiting") return p.status === "waiting";
    if (activeTab === "completed") return p.status === "completed" || p.status === "in_progress";
    return true;
  });

  const recruitingCount = posts.filter((p) => p.status === "recruiting" || p.status === "urgent").length;
  const waitingCount = posts.filter((p) => p.status === "waiting" || p.status === "in_progress").length;

  return (
    <>
      <Toast message={toast} />

      <div className="mx-auto max-w-3xl px-4 pb-24">

        {/* ── 헤더 ─────────────────────────────────────────────── */}
        <header className="sticky top-0 z-40 bg-gray-50 pt-6 pb-4">
          <div className="flex items-center justify-between">
            <div>
              <span className="font-[family-name:var(--font-fredoka)] text-[24px] font-bold text-orange-500">
                PawRelay
              </span>
              <p className="text-[13px] text-gray-400 mt-0.5">행복 동물 보호소</p>
            </div>
            <button className="flex h-10 w-10 items-center justify-center rounded-full bg-white border border-gray-200 text-gray-500 hover:bg-gray-50 transition-colors">
              <User size={18} />
            </button>
          </div>
        </header>

        {/* ── 통계 카드 ─────────────────────────────────────────── */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          <div className="rounded-2xl bg-white border border-gray-100 p-5">
            <p className="text-[12px] text-gray-400 mb-1">현재 모집 중인 공고</p>
            <p className="text-[32px] font-bold text-orange-500 leading-none">{recruitingCount}
              <span className="text-[16px] font-semibold text-gray-400 ml-1">건</span>
            </p>
          </div>
          <div className="rounded-2xl bg-white border border-gray-100 p-5">
            <p className="text-[12px] text-gray-400 mb-1">매칭 대기 / 봉사중</p>
            <p className="text-[32px] font-bold text-yellow-500 leading-none">{waitingCount}
              <span className="text-[16px] font-semibold text-gray-400 ml-1">건</span>
            </p>
          </div>
        </div>

        {/* ── 탭 필터 ────────────────────────────────────────────── */}
        <div className="flex gap-2 overflow-x-auto pb-1 mb-5 scrollbar-hide">
          {TABS.map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              className={`shrink-0 rounded-full px-4 py-2 text-[13px] font-semibold transition-all ${
                activeTab === key
                  ? "bg-orange-500 text-white shadow-sm"
                  : "bg-white border border-gray-200 text-gray-500 hover:border-orange-300"
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {/* ── 공고 리스트 ─────────────────────────────────────────── */}
        <div className="flex flex-col gap-3">
          {filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-gray-400">
              <p className="text-[14px]">해당 상태의 공고가 없습니다.</p>
            </div>
          ) : (
            filtered.map((post) => (
              <PostCard
                key={post.id}
                post={post}
                onShowApplicants={handleShowApplicants}
                onShowMatching={handleShowMatching}
              />
            ))
          )}
        </div>
      </div>

      {/* ── FAB ──────────────────────────────────────────────────── */}
      <Link
        href="/dashboard/posts/new"
        className="fixed bottom-6 right-6 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-orange-500 text-white shadow-lg shadow-orange-200 hover:bg-orange-600 transition-colors active:scale-95"
        aria-label="새 공고 등록"
      >
        <Plus size={24} />
      </Link>

      {/* ── 지원자 바텀 시트 ─────────────────────────────────────── */}
      <BottomSheet open={sheetType === "applicants"} onClose={closeSheet}>
        {selectedPost && (
          <>
            <div className="flex items-center justify-between pt-2 pb-4 border-b border-gray-100">
              <div>
                <h3 className="text-[16px] font-bold text-gray-900">
                  {selectedPost.animal.name} 공고 지원자
                </h3>
                <p className="text-[12px] text-gray-400 mt-0.5">
                  총 {selectedPost.volunteers.length}명 지원
                </p>
              </div>
              <button onClick={closeSheet} className="text-gray-400 hover:text-gray-600">
                <X size={20} />
              </button>
            </div>

            <div className="flex flex-col gap-2.5 mt-4">
              {selectedPost.volunteers.map((v) => (
                <div
                  key={v.id}
                  className="flex items-center gap-3 rounded-xl bg-gray-50 px-4 py-3.5"
                >
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-orange-100">
                    <span className="text-[13px] font-bold text-orange-600">
                      {v.name[0]}
                    </span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[14px] font-semibold text-gray-800">{v.name}</p>
                    <div className="flex items-center gap-1 text-[12px] text-gray-400">
                      <span>{v.from}</span>
                      <ArrowRight size={11} />
                      <span>{v.to}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <p className="mt-5 text-center text-[11px] leading-relaxed text-gray-400">
              체인 완성 후 LLM이 최적 팀을 자동 구성합니다.
            </p>
          </>
        )}
      </BottomSheet>

      {/* ── LLM 매칭 바텀 시트 ──────────────────────────────────── */}
      <BottomSheet open={sheetType === "matching"} onClose={closeSheet}>
        {selectedPost?.relayChain && (
          <>
            <div className="flex items-center justify-between pt-2 pb-4 border-b border-gray-100">
              <div>
                <h3 className="text-[16px] font-bold text-gray-900">LLM 최적 매칭 결과</h3>
                <p className="text-[12px] text-gray-400 mt-0.5">
                  {selectedPost.animal.name} ·{" "}
                  {selectedPost.origin} → {selectedPost.destination}
                </p>
              </div>
              <button onClick={closeSheet} className="text-gray-400 hover:text-gray-600">
                <X size={20} />
              </button>
            </div>

            {/* 릴레이 체인 시각화 */}
            <div className="mt-5 mb-4">
              <p className="text-[12px] font-semibold text-gray-400 uppercase tracking-wide mb-3">
                릴레이 체인
              </p>
              <div className="flex flex-col gap-0">
                {selectedPost.relayChain.map((seg, i) => (
                  <div key={i} className="flex gap-3">
                    {/* 타임라인 선 */}
                    <div className="flex flex-col items-center">
                      <div className="h-3 w-3 rounded-full bg-orange-400 ring-2 ring-orange-100 mt-1 shrink-0" />
                      {i < selectedPost.relayChain!.length - 1 && (
                        <div className="w-0.5 flex-1 bg-orange-100 my-1" />
                      )}
                    </div>
                    {/* 내용 */}
                    <div className="pb-5">
                      <div className="rounded-xl bg-orange-50 border border-orange-100 px-4 py-3">
                        <div className="flex items-center justify-between gap-3 mb-1">
                          <p className="text-[14px] font-bold text-gray-800">{seg.volunteer}</p>
                          <span className="text-[11px] text-gray-400">{seg.time}</span>
                        </div>
                        <div className="flex items-center gap-1.5 text-[12px] text-gray-500">
                          <span>{seg.from}</span>
                          <ArrowRight size={11} className="text-orange-300 shrink-0" />
                          <span>{seg.to}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                {/* 도착 */}
                <div className="flex gap-3">
                  <div className="flex flex-col items-center">
                    <div className="h-3 w-3 rounded-full bg-green-400 ring-2 ring-green-100 mt-1 shrink-0" />
                  </div>
                  <p className="text-[13px] font-semibold text-green-600 mt-0.5">보호소 도착 🏠</p>
                </div>
              </div>
            </div>

            {/* LLM 매칭 이유 */}
            {selectedPost.matchingReason && (
              <div className="rounded-xl bg-gray-50 border border-gray-100 px-4 py-3.5 mb-5">
                <p className="text-[11px] font-semibold text-gray-400 mb-1">AI 매칭 이유</p>
                <p className="text-[13px] text-gray-600 leading-relaxed">
                  {selectedPost.matchingReason}
                </p>
              </div>
            )}

            {/* 버튼 */}
            <div className="flex flex-col gap-2.5">
              <button
                onClick={handleApprove}
                className="h-14 w-full rounded-2xl bg-orange-500 text-[15px] font-bold text-white shadow-md shadow-orange-100 transition-all active:scale-[0.97] hover:bg-orange-600"
              >
                이 릴레이 팀으로 최종 승인
              </button>
              <button
                onClick={handleReject}
                className="h-12 w-full rounded-2xl border border-gray-200 text-[14px] font-semibold text-gray-500 transition-colors hover:bg-gray-50"
              >
                거절 / 재매칭 요청
              </button>
            </div>
          </>
        )}
      </BottomSheet>
    </>
  );
}
