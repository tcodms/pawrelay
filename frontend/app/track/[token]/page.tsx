"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Image from "next/image";
import { CheckCircle2, Car, AlertTriangle, Circle, Loader2, Clock } from "lucide-react";
import KakaoMap from "@/components/KakaoMap";
import type { MapMarker, LatLng } from "@/components/KakaoMap";
import { useWebSocket } from "@/hooks/useWebSocket";
import type { WsPayloadMap } from "@/hooks/useWebSocket";
import { getPublicPost } from "@/lib/api/posts";
import type { PublicPost, PublicPostCheckpoint } from "@/lib/api/posts";

// ── 상수 ───────────────────────────────────────────────────────────────────

const SIZE_LABEL: Record<string, string> = {
  small: "소형",
  medium: "중형",
  large: "대형",
};

// ── 유틸 ───────────────────────────────────────────────────────────────────

function formatDate(dateStr: string): string {
  const [y, m, d] = dateStr.split("-");
  return `${y}년 ${Number(m)}월 ${Number(d)}일`;
}

function formatTime(isoStr: string): string {
  const date = new Date(isoStr);
  const h = date.getHours().toString().padStart(2, "0");
  const m = date.getMinutes().toString().padStart(2, "0");
  return `${h}:${m}`;
}

function buildMarkers(checkpoints: PublicPostCheckpoint[]): MapMarker[] {
  return checkpoints
    .filter((cp) => cp.latitude != null && cp.longitude != null)
    .map((cp) => ({ latitude: cp.latitude, longitude: cp.longitude, type: "checkpoint" as const }));
}

function buildPolyline(checkpoints: PublicPostCheckpoint[]): LatLng[] {
  return checkpoints
    .filter((cp) => cp.latitude != null && cp.longitude != null)
    .map((cp) => ({ latitude: cp.latitude, longitude: cp.longitude }));
}

type RelayStatus = "pre_transit" | "in_transit" | "completed";

function getRelayStatus(post: PublicPost): RelayStatus {
  if (post.current_segment) return "in_transit";
  if (post.timeline.length > 0) return "completed";
  return "pre_transit";
}

type SegmentStatus = "completed" | "in_progress" | "delayed" | "waiting";

function getSegmentStatus(order: number, post: PublicPost): SegmentStatus {
  if (post.timeline.some((t) => t.segment_order === order)) return "completed";
  if (post.current_segment?.order === order) {
    return post.current_segment.status === "delayed" ? "delayed" : "in_progress";
  }
  return "waiting";
}

function getSegmentsToShow(post: PublicPost): number[] {
  const completed = post.timeline.map((t) => t.segment_order);
  const current = post.current_segment?.order ?? null;
  const max = Math.max(...completed, current ?? 0, 0);
  if (max === 0) return [1];
  const until = current !== null ? Math.min(max + 1, 2) : max;
  return Array.from({ length: until }, (_, i) => i + 1);
}

// ── 서브 컴포넌트 ───────────────────────────────────────────────────────────

function LoadingScreen() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="flex flex-col items-center gap-3">
        <Loader2 className="h-8 w-8 animate-spin text-[#EEA968]" />
        <p className="text-[14px] text-gray-400">이송 현황을 불러오는 중...</p>
      </div>
    </main>
  );
}

function ErrorScreen() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-50 px-6">
      <div className="flex flex-col items-center gap-3 text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-gray-100">
          <span className="text-2xl">🔗</span>
        </div>
        <p className="text-[16px] font-bold text-gray-700">조회할 수 없습니다</p>
        <p className="text-[13px] text-gray-400 leading-relaxed">
          링크가 만료되었거나 잘못된 주소입니다.
        </p>
      </div>
    </main>
  );
}

function AnimalCard({ post }: { post: PublicPost }) {
  const { animal_info, scheduled_date, origin, destination } = post;
  return (
    <div className="mx-4 mt-3 rounded-2xl bg-white p-3 shadow-sm border border-gray-100">
      <div className="flex items-center gap-3">
        {animal_info.photo_url ? (
          <Image
            src={animal_info.photo_url}
            alt={animal_info.name}
            width={48}
            height={48}
            className="h-12 w-12 rounded-xl object-cover shrink-0"
          />
        ) : (
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-orange-50 shrink-0">
            <span className="text-xl">🐾</span>
          </div>
        )}
        <div>
          <p className="text-[15px] font-bold text-gray-700">{animal_info.name}</p>
          <p className="text-[12px] text-gray-400 mt-0.5">
            {SIZE_LABEL[animal_info.size]} · {formatDate(scheduled_date)}
          </p>
        </div>
      </div>
      <div className="mt-2.5 pt-2.5 border-t border-gray-100 flex items-center gap-1.5">
        <span className="text-[12px] font-medium text-gray-600">{origin}</span>
        <span className="text-gray-300 text-[11px]">→</span>
        <span className="text-[12px] font-medium text-gray-600">{destination}</span>
      </div>
    </div>
  );
}

function SegmentItem({
  order,
  post,
  totalSegments,
}: {
  order: number;
  post: PublicPost;
  totalSegments: number;
}) {
  const status = getSegmentStatus(order, post);
  const completedAt = post.timeline.find((t) => t.segment_order === order)?.completed_at;
  const isWaiting = status === "waiting";
  const locationLabel =
    order === 1 ? `${post.origin} 출발` :
    order === totalSegments ? `${post.destination} 도착` : null;

  return (
    <div className="flex items-center gap-2.5 py-2.5 border-b border-gray-100 last:border-0">
      {status === "completed" && <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />}
      {status === "in_progress" && <Car className="h-4 w-4 text-[#EEA968] shrink-0" />}
      {status === "delayed" && <AlertTriangle className="h-4 w-4 text-orange-400 shrink-0" />}
      {status === "waiting" && <Circle className="h-4 w-4 text-gray-300 shrink-0" />}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <span className={`text-[13px] font-semibold ${isWaiting ? "text-gray-300" : "text-gray-700"}`}>
            {order}구간
          </span>
          {status === "in_progress" && <span className="text-[11px] text-[#EEA968]">이송 중</span>}
          {status === "delayed" && <span className="text-[11px] text-orange-400">지연 중</span>}
          {status === "completed" && completedAt && (
            <span className="text-[11px] text-gray-400">완료 {formatTime(completedAt)}</span>
          )}
          {status === "waiting" && <span className="text-[11px] text-gray-300">대기 중</span>}
        </div>
        {locationLabel && (
          <p className={`text-[11px] mt-0.5 ${isWaiting ? "text-gray-300" : "text-gray-400"}`}>
            {locationLabel}
          </p>
        )}
      </div>
    </div>
  );
}

function StatusBanner({ status }: { status: RelayStatus }) {
  if (status === "pre_transit") return (
    <div className="mx-4 mt-2.5 flex items-center gap-2 rounded-2xl bg-gray-50 border border-gray-100 px-4 py-2.5">
      <Clock className="h-4 w-4 text-gray-400 shrink-0" />
      <p className="text-[12px] text-gray-500">아직 이송이 시작되지 않았습니다</p>
    </div>
  );
  if (status === "completed") return (
    <div className="mx-4 mt-2.5 flex items-center gap-2 rounded-2xl bg-green-50 border border-green-100 px-4 py-2.5">
      <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />
      <p className="text-[12px] font-semibold text-green-600">이송이 완료되었습니다</p>
    </div>
  );
  return null;
}

export function TrackContent({
  post,
  checkpoints,
}: {
  post: PublicPost;
  checkpoints: PublicPostCheckpoint[];
}) {
  const segments = getSegmentsToShow(post);
  const markers = buildMarkers(checkpoints);
  const polyline = buildPolyline(checkpoints);
  const relayStatus = getRelayStatus(post);

  return (
    <main className="min-h-screen bg-gray-50 pb-8">
      <div className="bg-white px-4 pt-8 pb-3 border-b border-gray-100">
        <p className="font-[family-name:var(--font-fredoka)] text-[18px] font-bold text-[#EEA968] leading-none">
          PawRelay
        </p>
        <p className="text-[15px] font-bold text-gray-700 mt-0.5">실시간 이송 현황</p>
      </div>

      <AnimalCard post={post} />
      <StatusBanner status={relayStatus} />

      <div className="mx-4 mt-2.5 rounded-2xl bg-white shadow-sm border border-gray-100 overflow-hidden">
        <KakaoMap className="w-full h-[220px]" markers={markers} polyline={polyline} />
        <div className="px-4 pb-1">
          <p className="text-[12px] font-bold text-gray-500 pt-3 pb-1">이송 현황</p>
          {segments.map((order) => (
            <SegmentItem key={order} order={order} post={post} totalSegments={segments.length} />
          ))}
        </div>
      </div>

      <p className="mt-5 px-4 text-center text-[11px] text-gray-300">
        봉사자 실명·연락처는 공개되지 않습니다
      </p>
    </main>
  );
}

// ── 메인 페이지 ─────────────────────────────────────────────────────────────

export default function TrackPage() {
  const { token } = useParams<{ token: string }>();
  const [post, setPost] = useState<PublicPost | null>(null);
  const [pageStatus, setPageStatus] = useState<"loading" | "error" | "ready">("loading");
  const [checkpoints, setCheckpoints] = useState<PublicPostCheckpoint[]>([]);

  useEffect(() => {
    getPublicPost(token)
      .then((data) => {
        setPost(data);
        setCheckpoints(data.checkpoints);
        setPageStatus("ready");
      })
      .catch(() => setPageStatus("error"));
  }, [token]);

  useWebSocket({
    shareToken: token,
    enabled: pageStatus === "ready",
    onEvent: (name, payload) => {
      if (name !== "checkpoint.updated") return;
      const { latitude, longitude, recorded_at } = payload as WsPayloadMap["checkpoint.updated"];
      if (latitude == null || longitude == null) return;
      setCheckpoints((prev) => [...prev, { latitude, longitude, recorded_at }]);
    },
  });

  if (pageStatus === "loading") return <LoadingScreen />;
  if (pageStatus === "error" || !post) return <ErrorScreen />;
  return <TrackContent post={post} checkpoints={checkpoints} />;
}
