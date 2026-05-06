"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { ArrowRight, Calendar, MapPin, CheckCircle2, ChevronRight } from "lucide-react";
import { getMySchedules } from "@/lib/api/chatbot";
import type { ScheduleItem } from "@/lib/api/chatbot";
import { getMySegments } from "@/lib/api/matching";
import type { MySegment } from "@/lib/api/matching";

// ── 상수 ──────────────────────────────────────────────────────────────────────

const SIZE_LABEL: Record<string, string> = {
  small: "소형", medium: "중형", large: "대형",
};

const SCHEDULE_STATUS_LABEL: Record<string, { label: string; cls: string }> = {
  available: { label: "대기 중",   cls: "bg-green-100 text-green-700" },
  matched:   { label: "매칭 완료", cls: "bg-[#FDF3EC] text-[#C17A3A]" },
  expired:   { label: "만료",      cls: "bg-gray-100 text-gray-400" },
};

const SEGMENT_STATUS: Record<string, { label: string; cls: string }> = {
  pending:     { label: "수락 대기 중", cls: "bg-orange-50 text-orange-500" },
  accepted:    { label: "수락 완료",    cls: "bg-green-50 text-green-600" },
  in_progress: { label: "이동 중",      cls: "bg-blue-50 text-blue-600" },
  completed:   { label: "완료",         cls: "bg-gray-100 text-gray-500" },
};

type Tab = "진행중" | "완료" | "취소";

// ── 카드 컴포넌트 ──────────────────────────────────────────────────────────────

function RouteCard({ s }: { s: ScheduleItem }) {
  return (
    <div className="rounded-2xl bg-white border border-gray-100 shadow-sm px-4 py-3.5">
      <div className="flex items-center justify-between mb-1.5">
        <div className="flex items-center gap-1.5 text-[14px] font-semibold text-gray-800">
          <span>{s.origin_area}</span>
          <ArrowRight size={12} className="text-gray-300" />
          <span>{s.destination_area}</span>
        </div>
        <span className={`text-[11px] px-1.5 py-0.5 rounded-full font-medium ${SCHEDULE_STATUS_LABEL[s.status]?.cls ?? "bg-gray-100 text-gray-400"}`}>
          {SCHEDULE_STATUS_LABEL[s.status]?.label ?? s.status}
        </span>
      </div>
      <div className="flex items-center gap-3 text-[12px] text-gray-400">
        <span className="flex items-center gap-1">
          <Calendar size={11} />
          {s.available_date}{s.available_time && ` · ${s.available_time}`}
        </span>
        <span className="px-1.5 py-0.5 rounded-full bg-gray-100 text-gray-500">
          {SIZE_LABEL[s.max_animal_size] ?? s.max_animal_size} 가능
        </span>
      </div>
    </div>
  );
}

function AppliedCard({ s }: { s: ScheduleItem }) {
  return (
    <div className="rounded-2xl bg-white border border-gray-100 shadow-sm overflow-hidden">
      <div className="flex gap-3.5 p-4">
        <div className="relative h-[60px] w-[60px] shrink-0 rounded-xl overflow-hidden bg-gray-100">
          {s.applied_post?.animal_photo_url ? (
            <Image src={s.applied_post.animal_photo_url} alt={s.applied_post.animal_name} fill className="object-cover" />
          ) : (
            <div className="flex h-full items-center justify-center text-2xl">🐾</div>
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[15px] font-bold text-gray-900">{s.applied_post?.animal_name ?? "-"}</span>
            <span className="text-[11px] px-1.5 py-0.5 rounded-full bg-gray-100 text-gray-500">
              {SIZE_LABEL[s.applied_post?.animal_size ?? ""] ?? "-"}
            </span>
            <span className={`text-[11px] px-1.5 py-0.5 rounded-full font-medium ${SCHEDULE_STATUS_LABEL[s.status]?.cls ?? "bg-gray-100 text-gray-400"}`}>
              {SCHEDULE_STATUS_LABEL[s.status]?.label ?? s.status}
            </span>
          </div>
          <div className="flex items-center gap-1 text-[12px] text-gray-500 mb-1">
            <MapPin size={11} className="text-[#EEA968] shrink-0" />
            <span className="truncate">{s.applied_post?.origin}</span>
            <ArrowRight size={10} className="shrink-0 text-gray-300" />
            <span className="truncate">{s.applied_post?.destination}</span>
          </div>
          <div className="flex items-center gap-1 text-[12px] text-gray-400">
            <Calendar size={11} className="shrink-0" />
            <span>{s.available_date}</span>
            {s.available_time && <span>· {s.available_time}</span>}
          </div>
        </div>
      </div>
      <div className="border-t border-gray-100 px-4 py-2.5 flex items-center gap-1.5 text-[12px] text-gray-500">
        <CheckCircle2 size={12} className="text-[#EEA968]" />
        <span>내 구간:</span>
        <span className="font-medium text-gray-700">{s.origin_area}</span>
        <ArrowRight size={10} className="text-gray-300" />
        <span className="font-medium text-gray-700">{s.destination_area}</span>
      </div>
    </div>
  );
}

function SegmentCard({ seg }: { seg: MySegment }) {
  const cfg = SEGMENT_STATUS[seg.status] ?? { label: seg.status, cls: "bg-red-50 text-red-400" };
  return (
    <Link
      href={`/volunteer/matching/${seg.segment_id}`}
      className="flex items-center gap-3.5 rounded-2xl bg-white border border-[#EEA968]/30 shadow-sm px-4 py-3.5 active:scale-[0.98] transition-transform"
    >
      <div className="relative h-12 w-12 shrink-0 rounded-xl overflow-hidden bg-gray-100">
        {seg.animal_photo_url ? (
          <Image src={seg.animal_photo_url} alt={seg.animal_name} fill className="object-cover" />
        ) : (
          <div className="flex h-full items-center justify-center text-xl">🐾</div>
        )}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-[15px] font-bold text-gray-900">{seg.animal_name}</span>
          <span className={`text-[11px] px-1.5 py-0.5 rounded-full font-semibold ${cfg.cls}`}>{cfg.label}</span>
        </div>
        <div className="flex items-center gap-1 text-[12px] text-gray-500">
          <span className="truncate">{seg.pickup_location}</span>
          <ArrowRight size={10} className="text-gray-300 shrink-0" />
          <span className="truncate">{seg.dropoff_location}</span>
        </div>
        {seg.scheduled_date && (
          <div className="flex items-center gap-1 text-[11px] text-gray-400 mt-0.5">
            <Calendar size={10} />
            <span>{seg.scheduled_date}{seg.depart_time && ` · ${seg.depart_time} 출발`}</span>
          </div>
        )}
      </div>
      <ChevronRight size={16} className="text-gray-300 shrink-0" />
    </Link>
  );
}

function SectionDivider({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-3 pt-2 pb-1">
      <span className="text-[12px] font-semibold text-gray-400 shrink-0">{label}</span>
      <div className="flex-1 h-px bg-gray-200" />
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <p className="text-[36px] mb-3">🐾</p>
      <p className="text-[14px] font-semibold text-gray-600 mb-1">내역이 없어요</p>
      <p className="text-[12px] text-gray-400">챗봇에서 동선을 등록해보세요.</p>
    </div>
  );
}

// ── 탭 콘텐츠 ─────────────────────────────────────────────────────────────────

function InProgressTab({ schedules, segments }: { schedules: ScheduleItem[]; segments: MySegment[] }) {
  const routes     = schedules.filter((s) => s.post_id === null && s.status !== "expired");
  const applied    = schedules.filter((s) => s.post_id !== null && s.status !== "expired");
  const waiting    = segments.filter((s) => s.status === "pending");
  const inProgress = segments.filter((s) => s.status === "accepted" || s.status === "in_progress");

  return (
    <div className="space-y-4">
      <SectionDivider label="등록된 동선" />
      {routes.length > 0 ? (
        <div className="space-y-2.5">{routes.map((s) => <RouteCard key={s.id} s={s} />)}</div>
      ) : (
        <p className="text-[13px] text-gray-300 px-1">등록된 동선이 없어요.</p>
      )}

      <SectionDivider label="매칭 제안 대기" />
      {(applied.length > 0 || waiting.length > 0) ? (
        <div className="space-y-2.5">
          {applied.map((s) => <AppliedCard key={s.id} s={s} />)}
          {waiting.map((seg) => <SegmentCard key={seg.segment_id} seg={seg} />)}
        </div>
      ) : (
        <p className="text-[13px] text-gray-300 px-1">매칭 제안이 없어요.</p>
      )}

      <SectionDivider label="봉사 진행중" />
      {inProgress.length > 0 ? (
        <div className="space-y-2.5">{inProgress.map((seg) => <SegmentCard key={seg.segment_id} seg={seg} />)}</div>
      ) : (
        <p className="text-[13px] text-gray-300 px-1">진행 중인 봉사가 없어요.</p>
      )}
    </div>
  );
}

function CompletedTab({ segments }: { segments: MySegment[] }) {
  const completed = segments.filter((s) => s.status === "completed");
  if (completed.length === 0) return <EmptyState />;
  return (
    <div className="space-y-2.5">
      {completed.map((seg) => <SegmentCard key={seg.segment_id} seg={seg} />)}
    </div>
  );
}

function CancelledTab({ schedules, segments }: { schedules: ScheduleItem[]; segments: MySegment[] }) {
  const expiredSchedules  = schedules.filter((s) => s.status === "expired");
  const cancelledSegments = segments.filter(
    (s) => !["pending", "accepted", "in_progress", "completed"].includes(s.status)
  );
  if (expiredSchedules.length === 0 && cancelledSegments.length === 0) return <EmptyState />;
  return (
    <div className="space-y-6">
      {cancelledSegments.length > 0 && (
        <section>
          <h2 className="text-[13px] font-bold text-gray-400 mb-2.5 px-1">취소된 봉사</h2>
          <div className="space-y-2.5">{cancelledSegments.map((seg) => <SegmentCard key={seg.segment_id} seg={seg} />)}</div>
        </section>
      )}
      {expiredSchedules.length > 0 && (
        <section>
          <h2 className="text-[13px] font-bold text-gray-400 mb-2.5 px-1">만료된 동선</h2>
          <div className="space-y-2.5">{expiredSchedules.map((s) => <RouteCard key={s.id} s={s} />)}</div>
        </section>
      )}
    </div>
  );
}

// ── 메인 페이지 ───────────────────────────────────────────────────────────────

export default function ServicesPage() {
  const [tab, setTab] = useState<Tab>("진행중");
  const [schedules, setSchedules] = useState<ScheduleItem[]>([]);
  const [segments, setSegments] = useState<MySegment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let done = 0;
    const finish = () => { if (++done === 2) setLoading(false); };
    getMySchedules().then(setSchedules).catch(() => {}).finally(finish);
    getMySegments().then(setSegments).catch(() => {}).finally(finish);
  }, []);

  const TABS: Tab[] = ["진행중", "완료", "취소"];

  return (
    <main className="min-h-screen bg-gray-50">
      <header className="sticky top-0 z-10 bg-white border-b border-gray-100">
        <div className="mx-auto max-w-2xl px-5 pt-4 pb-3">
          <h1 className="text-[18px] font-bold text-gray-900 leading-tight">내 릴레이</h1>
          <p className="text-[11px] text-gray-400 mt-0.5">나의 봉사 현황을 확인해요.</p>
        </div>
        <div className="mx-auto max-w-2xl flex px-4">
          {TABS.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`flex-1 py-2.5 text-[13px] font-semibold border-b-2 transition-colors ${
                tab === t ? "border-[#EEA968] text-[#EEA968]" : "border-transparent text-gray-400"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </header>

      {loading ? (
        <div className="flex justify-center pt-20">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-[#EEA968] border-t-transparent" />
        </div>
      ) : (
        <div className="mx-auto max-w-2xl px-4 pt-5 pb-24">
          {tab === "진행중" && <InProgressTab schedules={schedules} segments={segments} />}
          {tab === "완료"   && <CompletedTab segments={segments} />}
          {tab === "취소"   && <CancelledTab schedules={schedules} segments={segments} />}
        </div>
      )}
    </main>
  );
}
