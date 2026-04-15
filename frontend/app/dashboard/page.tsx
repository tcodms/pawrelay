"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { User, Plus, X, ChevronRight, ArrowRight, Users } from "lucide-react";
import { getPosts, Post } from "@/lib/api/posts";
import { approveShelterMatching, rejectShelterMatching } from "@/lib/api/matching";
import { getShelterProfile } from "@/lib/api/shelter";
import { StatusBadge, SizeBadge } from "@/components/ui/PostBadges";

// ── Types ──────────────────────────────────────────────────────────────────────

type TabKey = "all" | "recruiting" | "waiting" | "in_progress" | "completed";

// ── Sub-components ─────────────────────────────────────────────────────────────

const TABS: { key: TabKey; label: string; dot: string }[] = [
  { key: "all",         label: "전체",    dot: "bg-gray-400" },
  { key: "recruiting",  label: "모집 중", dot: "bg-green-500" },
  { key: "waiting",     label: "대기 중", dot: "bg-yellow-400" },
  { key: "in_progress", label: "봉사 중", dot: "bg-[#EEA968]" },
  { key: "completed",   label: "종료",    dot: "bg-gray-300" },
];

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
    <div
      role="status"
      aria-live="polite"
      aria-atomic="true"
      className="fixed inset-x-0 top-5 z-[60] flex justify-center px-4 animate-fade-in"
    >
      <div className="flex items-center gap-2.5 rounded-2xl bg-gray-900 px-5 py-3.5 shadow-xl">
        <svg aria-hidden="true" className="shrink-0 text-green-400" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
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
  const hasAction = isWaiting || isRecruiting || isUrgent;

  return (
    <div className="rounded-2xl bg-white border border-gray-100 transition-shadow hover:shadow-md">
      {/* 상세 페이지 링크 — 카드 정보 영역 전체 */}
      <Link
        href={`/dashboard/posts/${post.id}`}
        className={`block p-5 ${hasAction ? "pb-3" : ""}`}
      >
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex items-center gap-2 flex-wrap">
            <StatusBadge status={post.status} variant="sm" />
            <SizeBadge size={post.animal.size} variant="sm" />
          </div>
          <span className="text-[12px] text-gray-400 shrink-0">{post.scheduledDate}</span>
        </div>

        <p className="text-[16px] font-bold text-gray-900 mb-1">{post.animal.name}</p>
        <div className="flex items-center gap-1.5 text-[13px] text-gray-500 mb-4">
          <span>{post.origin}</span>
          <ArrowRight size={13} className="text-gray-300 shrink-0" />
          <span>{post.destination}</span>
        </div>

        <div className="flex items-center gap-1.5 text-[13px] text-gray-500">
          <Users size={14} className="text-gray-400" />
          <span>현재 지원: <span className="font-semibold text-gray-700">{post.volunteers.length}명</span></span>
        </div>
      </Link>

      {/* 액션 버튼 — Link 바깥에 배치하여 중첩 방지 */}
      {hasAction && (
        <div className="px-5 pb-5">
          {isWaiting && (
            <button
              onClick={() => onShowMatching(post)}
              className="w-full flex items-center justify-between px-4 rounded-xl py-2.5 text-[13px] font-semibold bg-yellow-50 text-yellow-700 hover:bg-yellow-100 transition-colors active:scale-[0.98]"
            >
              <span className="flex-1 text-center">매칭 결과</span>
              <ChevronRight size={15} className="text-yellow-400" />
            </button>
          )}
          {(isRecruiting || isUrgent) && (
            <button
              onClick={() => onShowApplicants(post)}
              className={`w-full flex items-center justify-between px-4 rounded-xl py-2.5 text-[13px] font-semibold transition-colors active:scale-[0.98] ${
                isUrgent
                  ? "bg-red-50 text-red-600 hover:bg-red-100"
                  : "bg-green-50 text-green-700 hover:bg-green-100"
              }`}
            >
              <span className="flex-1 text-center">지원자 목록</span>
              <ChevronRight size={15} className={isUrgent ? "text-red-400" : "text-green-400"} />
            </button>
          )}
        </div>
      )}
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────────────

export default function DashboardPage() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [shelterName, setShelterName] = useState("보호소");
  const [activeTab, setActiveTab] = useState<TabKey>("all");
  const [selectedPost, setSelectedPost] = useState<Post | null>(null);
  const [sheetType, setSheetType] = useState<"applicants" | "matching" | null>(null);
  const [toast, setToast] = useState("");
  const toastTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    getPosts()
      .then(setPosts)
      .catch(() => {})
      .finally(() => setLoading(false));
    getShelterProfile()
      .then((p) => setShelterName(p.name))
      .catch(() => {});
    return () => { if (toastTimerRef.current) clearTimeout(toastTimerRef.current); };
  }, []);

  function showToast(msg: string) {
    if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    setToast(msg);
    toastTimerRef.current = setTimeout(() => setToast(""), 4000);
  }

  function closeSheet() {
    setSelectedPost(null);
    setSheetType(null);
  }

  async function handleApprove() {
    if (!selectedPost) return;
    try {
      await approveShelterMatching(selectedPost.id);
      setPosts((prev) =>
        prev.map((p) => p.id === selectedPost.id ? { ...p, status: "in_progress" } : p)
      );
      closeSheet();
      showToast("릴레이 매칭이 확정되었습니다! 모든 봉사자에게 안내 이메일이 발송됩니다.");
    } catch {
      showToast("처리 중 오류가 발생했습니다. 다시 시도해 주세요.");
    }
  }

  async function handleReject() {
    if (!selectedPost) return;
    try {
      await rejectShelterMatching(selectedPost.id);
      closeSheet();
      showToast("재매칭 요청이 접수되었습니다. 다음 배치 시 재처리됩니다.");
    } catch {
      showToast("처리 중 오류가 발생했습니다. 다시 시도해 주세요.");
    }
  }

  const filtered = posts.filter((p) => {
    if (activeTab === "all")         return true;
    if (activeTab === "recruiting")  return p.status === "recruiting" || p.status === "urgent";
    if (activeTab === "waiting")     return p.status === "waiting";
    if (activeTab === "in_progress") return p.status === "in_progress";
    if (activeTab === "completed")   return p.status === "completed";
    return true;
  });

  const recruitingCount = posts.filter((p) => p.status === "recruiting" || p.status === "urgent").length;
  const waitingCount    = posts.filter((p) => p.status === "waiting").length;

  return (
    <>
      <Toast message={toast} />

      <div className="mx-auto max-w-3xl px-4 pb-24">

        {/* ── 헤더 ─────────────────────────────────────────────── */}
        <header className="sticky top-0 z-40 bg-gray-50 pt-6 pb-4">
          <div className="flex items-center justify-between">
            <div>
              <span className="font-[family-name:var(--font-fredoka)] text-[24px] font-bold text-[#EEA968]">
                PawRelay
              </span>
              <p className="text-[13px] text-gray-400 mt-0.5">{shelterName}</p>
            </div>
            <Link
              href="/dashboard/profile"
              aria-label="프로필"
              className="flex h-10 w-10 items-center justify-center rounded-full bg-white border border-gray-200 text-gray-500 hover:bg-gray-50 transition-colors"
            >
              <User size={18} />
            </Link>
          </div>
        </header>

        {/* ── 통계 카드 ─────────────────────────────────────────── */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          <div className="rounded-2xl bg-white border border-gray-100 px-4 py-3 flex flex-col gap-1">
            <p className="text-[12px] text-gray-400">모집중 공고</p>
            <p className="text-[28px] font-bold text-[#EEA968] leading-none">{recruitingCount}
              <span className="text-[14px] font-semibold text-gray-400 ml-1">건</span>
            </p>
          </div>
          <div className="rounded-2xl bg-white border border-gray-100 px-4 py-3 flex flex-col gap-1">
            <p className="text-[12px] text-gray-400">매칭 대기 공고</p>
            <p className="text-[28px] font-bold text-yellow-500 leading-none">{waitingCount}
              <span className="text-[14px] font-semibold text-gray-400 ml-1">건</span>
            </p>
          </div>
        </div>

        {/* ── 탭 필터 ────────────────────────────────────────────── */}
        <div className="flex border-b border-gray-100 mb-5 overflow-x-auto [&::-webkit-scrollbar]:hidden">
          {TABS.map(({ key, label, dot }) => {
            const isActive = activeTab === key;
            return (
              <button
                key={key}
                onClick={() => setActiveTab(key)}
                aria-current={isActive ? "true" : undefined}
                className={`flex shrink-0 items-center gap-1.5 px-3 pb-2.5 pt-1 text-[12px] transition-all relative ${
                  isActive
                    ? "font-bold text-gray-900"
                    : "font-medium text-gray-400 hover:text-gray-600"
                }`}
              >
                <span className={`h-1.5 w-1.5 rounded-full shrink-0 ${dot}`} />
                {label}
                {isActive && (
                  <span className="absolute bottom-0 left-0 right-0 h-0.5 rounded-full bg-[#EEA968]" />
                )}
              </button>
            );
          })}
        </div>

        {/* ── 공고 리스트 ─────────────────────────────────────────── */}
        <div className="flex flex-col gap-3">
          {loading ? (
            <div className="flex justify-center py-20">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-[#EEA968] border-t-transparent" />
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-gray-400">
              <p className="text-[14px]">해당 상태의 공고가 없습니다.</p>
            </div>
          ) : (
            filtered.map((post) => (
              <PostCard
                key={post.id}
                post={post}
                onShowApplicants={(p) => { setSelectedPost(p); setSheetType("applicants"); }}
                onShowMatching={(p)   => { setSelectedPost(p); setSheetType("matching"); }}
              />
            ))
          )}
        </div>
      </div>

      {/* ── FAB ──────────────────────────────────────────────────── */}
      <Link
        href="/dashboard/posts/new"
        className="fixed bottom-6 right-6 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-[#EEA968] text-white shadow-lg shadow-[#EEA968]/25 hover:bg-[#D99A55] transition-colors active:scale-95"
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
              <button onClick={closeSheet} aria-label="닫기" className="text-gray-400 hover:text-gray-600">
                <X size={20} />
              </button>
            </div>

            <div className="flex flex-col gap-2.5 mt-4">
              {selectedPost.volunteers.map((v) => (
                <div key={v.id} className="flex items-center gap-3 rounded-xl bg-gray-50 px-4 py-3.5">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#FDF3EC]">
                    <span className="text-[13px] font-bold text-[#7A4A28]">{v.name[0]}</span>
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
          </>
        )}
      </BottomSheet>

      {/* ── LLM 매칭 바텀 시트 ──────────────────────────────────── */}
      <BottomSheet open={sheetType === "matching"} onClose={closeSheet}>
        {selectedPost?.relayChain && (
          <>
            <div className="flex items-center justify-between pt-2 pb-4 border-b border-gray-100">
              <div>
                <h3 className="text-[16px] font-bold text-gray-900">최종 매칭 결과</h3>
                <p className="text-[12px] text-gray-400 mt-0.5">
                  {selectedPost.animal.name} · {selectedPost.origin} → {selectedPost.destination}
                </p>
              </div>
              <button onClick={closeSheet} aria-label="닫기" className="text-gray-400 hover:text-gray-600">
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
                    <div className="flex flex-col items-center">
                      <div className="h-3 w-3 rounded-full bg-[#EEA968] ring-2 ring-[#FDF3EC] mt-1 shrink-0" />
                      {i < selectedPost.relayChain!.length - 1 && (
                        <div className="w-0.5 flex-1 bg-[#FDF3EC] my-1" />
                      )}
                    </div>
                    <div className="pb-5">
                      <div className="rounded-xl bg-[#FDF3EC] border border-[#EEA968]/20 px-4 py-3">
                        <div className="flex items-center justify-between gap-3 mb-1">
                          <p className="text-[14px] font-bold text-gray-800">{seg.volunteer}</p>
                          <span className="text-[11px] text-gray-400">{seg.time}</span>
                        </div>
                        <div className="flex items-center gap-1.5 text-[12px] text-gray-500">
                          <span>{seg.from}</span>
                          <ArrowRight size={11} className="text-[#EEA968]/60 shrink-0" />
                          <span>{seg.to}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
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

            <div className="flex flex-col gap-2.5">
              <button
                onClick={handleApprove}
                className="h-14 w-full rounded-2xl bg-[#EEA968] text-[15px] font-bold text-white shadow-md shadow-[#EEA968]/15 transition-all active:scale-[0.97] hover:bg-[#D99A55]"
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
