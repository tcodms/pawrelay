"use client";

import Image from "next/image";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import {
  Activity,
  CalendarDays,
  Clock3,
  MapPin,
  PawPrint,
  Route,
  Wifi,
} from "lucide-react";
import KakaoMap, { type LatLng, type MapMarker } from "@/components/KakaoMap";
import { ApiError } from "@/lib/api";
import {
  getPublicPost,
  type PublicCheckpoint,
  type PublicPostResponse,
} from "@/lib/api/posts";
import { useWebSocket } from "@/hooks/useWebSocket";

const SIZE_LABEL: Record<string, string> = {
  small: "소형",
  medium: "중형",
  large: "대형",
};

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("ko-KR", {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(new Date(value));
}

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("ko-KR", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function getSegmentLabel(status: string): string {
  if (status === "in_progress") return "이동 중";
  if (status === "completed") return "완료";
  if (status === "accepted") return "출발 대기";
  return status;
}

function buildMarkers(checkpoints: PublicCheckpoint[]): MapMarker[] {
  return checkpoints.map((checkpoint) => ({
    latitude: checkpoint.latitude,
    longitude: checkpoint.longitude,
    type: "checkpoint",
  }));
}

function buildPolyline(checkpoints: PublicCheckpoint[]): LatLng[] {
  return checkpoints.map((checkpoint) => ({
    latitude: checkpoint.latitude,
    longitude: checkpoint.longitude,
  }));
}

function SummaryCard({ post }: { post: PublicPostResponse }) {
  return (
    <section className="rounded-[28px] bg-white p-5 shadow-sm ring-1 ring-black/5">
      <div className="flex gap-4">
        <div className="relative h-24 w-24 shrink-0 overflow-hidden rounded-2xl bg-[#FDF3EC]">
          {post.animal_info.photo_url ? (
            <Image
              src={post.animal_info.photo_url}
              alt={post.animal_info.name}
              fill
              className="object-cover"
              sizes="96px"
            />
          ) : (
            <div className="flex h-full items-center justify-center text-[#EEA968]">
              <PawPrint size={30} />
            </div>
          )}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h1 className="truncate text-[22px] font-bold text-gray-900">
              {post.animal_info.name}
            </h1>
            <span className="rounded-full bg-gray-100 px-2.5 py-1 text-[11px] font-semibold text-gray-600">
              {SIZE_LABEL[post.animal_info.size] ?? post.animal_info.size}
            </span>
          </div>
          <p className="mt-1 text-[13px] font-medium text-gray-500">
            {formatDate(post.scheduled_date)} 이동 예정
          </p>
          <div className="mt-4 grid gap-2 text-[13px] text-gray-700">
            <div className="flex items-start gap-2">
              <MapPin size={16} className="mt-0.5 shrink-0 text-[#EEA968]" />
              <div className="min-w-0">
                <p className="font-semibold text-gray-800">출발</p>
                <p className="break-words text-gray-500">{post.origin}</p>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <Route size={16} className="mt-0.5 shrink-0 text-[#5B8DEF]" />
              <div className="min-w-0">
                <p className="font-semibold text-gray-800">도착</p>
                <p className="break-words text-gray-500">{post.destination}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
      {post.animal_info.notes ? (
        <div className="mt-4 rounded-2xl bg-[#FFF8F2] px-4 py-3 text-[13px] leading-relaxed text-gray-700">
          {post.animal_info.notes}
        </div>
      ) : null}
    </section>
  );
}

function StatusCard({
  post,
  liveMessage,
}: {
  post: PublicPostResponse;
  liveMessage: string | null;
}) {
  const lastCheckpoint = post.checkpoints[post.checkpoints.length - 1];

  return (
    <section className="rounded-[28px] bg-white p-5 shadow-sm ring-1 ring-black/5">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-[12px] font-semibold uppercase tracking-[0.18em] text-gray-400">
            Live Status
          </p>
          <h2 className="mt-1 text-[18px] font-bold text-gray-900">
            {post.current_segment
              ? `${post.current_segment.order}번 구간 ${getSegmentLabel(post.current_segment.status)}`
              : "실시간 이동 정보를 기다리는 중이에요"}
          </h2>
        </div>
        <div className="rounded-full bg-emerald-50 px-3 py-1.5 text-[12px] font-semibold text-emerald-700">
          체크포인트 {post.checkpoints.length}개
        </div>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <div className="rounded-2xl bg-gray-50 px-4 py-3">
          <div className="flex items-center gap-2 text-gray-500">
            <CalendarDays size={15} />
            <span className="text-[12px] font-semibold">예정일</span>
          </div>
          <p className="mt-2 text-[14px] font-semibold text-gray-800">
            {formatDate(post.scheduled_date)}
          </p>
        </div>
        <div className="rounded-2xl bg-gray-50 px-4 py-3">
          <div className="flex items-center gap-2 text-gray-500">
            <Clock3 size={15} />
            <span className="text-[12px] font-semibold">마지막 업데이트</span>
          </div>
          <p className="mt-2 text-[14px] font-semibold text-gray-800">
            {lastCheckpoint ? formatDateTime(lastCheckpoint.recorded_at) : "아직 기록 없음"}
          </p>
        </div>
      </div>

      <div className="mt-4 rounded-2xl border border-dashed border-[#EEA968]/30 bg-[#FFF8F2] px-4 py-3">
        <div className="flex items-start gap-2">
          <Wifi size={16} className="mt-0.5 shrink-0 text-[#EEA968]" />
          <p className="text-[13px] leading-relaxed text-gray-700">
            {liveMessage ?? "실시간 업데이트 연결을 대기 중입니다."}
          </p>
        </div>
      </div>
    </section>
  );
}

function MapSection({ checkpoints }: { checkpoints: PublicCheckpoint[] }) {
  const latest = checkpoints[checkpoints.length - 1];

  if (!latest) {
    return (
      <section className="rounded-[28px] bg-white p-5 shadow-sm ring-1 ring-black/5">
        <h2 className="text-[18px] font-bold text-gray-900">현재 위치</h2>
        <div className="mt-4 flex min-h-[260px] items-center justify-center rounded-3xl border border-dashed border-gray-200 bg-gray-50 text-center text-[13px] leading-relaxed text-gray-500">
          아직 위치 체크포인트가 기록되지 않았어요.
          <br />
          이동이 시작되면 이 화면에서 최신 위치를 볼 수 있어요.
        </div>
      </section>
    );
  }

  return (
    <section className="rounded-[28px] bg-white p-5 shadow-sm ring-1 ring-black/5">
      <h2 className="text-[18px] font-bold text-gray-900">현재 위치</h2>
      <p className="mt-1 text-[13px] text-gray-500">
        가장 최근 체크포인트 기준 위치를 표시합니다.
      </p>
      <div className="mt-4 overflow-hidden rounded-3xl">
        <KakaoMap
          latitude={latest.latitude}
          longitude={latest.longitude}
          level={6}
          className="h-[280px] w-full"
          markers={buildMarkers(checkpoints)}
          polyline={buildPolyline(checkpoints)}
        />
      </div>
    </section>
  );
}

function CheckpointSection({ checkpoints }: { checkpoints: PublicCheckpoint[] }) {
  return (
    <section className="rounded-[28px] bg-white p-5 shadow-sm ring-1 ring-black/5">
      <div className="flex items-center gap-2">
        <Activity size={18} className="text-[#5B8DEF]" />
        <h2 className="text-[18px] font-bold text-gray-900">체크포인트 기록</h2>
      </div>
      {checkpoints.length ? (
        <div className="mt-4 space-y-3">
          {checkpoints
            .slice()
            .reverse()
            .map((checkpoint, index) => (
              <div
                key={`${checkpoint.recorded_at}-${index}`}
                className="rounded-2xl border border-gray-100 bg-gray-50 px-4 py-3"
              >
                <div className="flex items-center justify-between gap-3">
                  <p className="text-[13px] font-semibold text-gray-800">
                    {formatDateTime(checkpoint.recorded_at)}
                  </p>
                  <span className="rounded-full bg-white px-2.5 py-1 text-[11px] font-medium text-gray-500">
                    {checkpoint.latitude.toFixed(4)}, {checkpoint.longitude.toFixed(4)}
                  </span>
                </div>
              </div>
            ))}
        </div>
      ) : (
        <p className="mt-4 text-[13px] text-gray-500">
          아직 기록된 체크포인트가 없습니다.
        </p>
      )}
    </section>
  );
}

function TimelineSection({ post }: { post: PublicPostResponse }) {
  return (
    <section className="rounded-[28px] bg-white p-5 shadow-sm ring-1 ring-black/5">
      <h2 className="text-[18px] font-bold text-gray-900">진행 타임라인</h2>
      <div className="mt-4 space-y-4">
        <div className="flex gap-3">
          <div className="mt-1 h-3 w-3 shrink-0 rounded-full bg-[#EEA968]" />
          <div>
            <p className="text-[14px] font-semibold text-gray-800">이동 등록</p>
            <p className="mt-1 text-[13px] text-gray-500">
              {post.origin}에서 {post.destination}까지의 릴레이 이동이 등록되었습니다.
            </p>
          </div>
        </div>
        {post.timeline.map((item) => (
          <div key={`${item.segment_order}-${item.completed_at}`} className="flex gap-3">
            <div className="mt-1 h-3 w-3 shrink-0 rounded-full bg-emerald-500" />
            <div>
              <p className="text-[14px] font-semibold text-gray-800">
                {item.segment_order}번 구간 완료
              </p>
              <p className="mt-1 text-[13px] text-gray-500">
                {formatDateTime(item.completed_at)}
              </p>
            </div>
          </div>
        ))}
        {post.current_segment ? (
          <div className="flex gap-3">
            <div className="mt-1 h-3 w-3 shrink-0 rounded-full bg-sky-500" />
            <div>
              <p className="text-[14px] font-semibold text-gray-800">
                현재 {post.current_segment.order}번 구간 진행 중
              </p>
              <p className="mt-1 text-[13px] text-gray-500">
                봉사자가 현재 구간을 이동하고 있습니다.
              </p>
            </div>
          </div>
        ) : null}
      </div>
    </section>
  );
}

export default function TrackPage() {
  const params = useParams();
  const token = params.token as string;
  const [post, setPost] = useState<PublicPostResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [reloadKey, setReloadKey] = useState(0);
  const [liveMessage, setLiveMessage] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const next = await getPublicPost(token);
        if (cancelled) return;
        setPost(next);
        setError(null);
      } catch (err) {
        if (cancelled) return;
        if (err instanceof ApiError && err.code === "POST_NOT_FOUND") {
          setError("유효하지 않은 조회 링크예요.");
        } else {
          setError("이동 현황을 불러오지 못했어요. 잠시 후 다시 시도해주세요.");
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    setIsLoading(true);
    void load();

    return () => {
      cancelled = true;
    };
  }, [token, reloadKey]);

  useWebSocket({
    shareToken: token,
    enabled: Boolean(token),
    onEvent: (eventName) => {
      if (eventName !== "checkpoint.updated") return;
      setLiveMessage("새 체크포인트가 도착해 이동 현황을 새로고침했어요.");
      setReloadKey((current) => current + 1);
    },
  });

  if (isLoading) {
    return (
      <main className="min-h-screen bg-[#F7F7FB] px-6 py-16">
        <div className="mx-auto flex max-w-3xl items-center justify-center rounded-[28px] bg-white p-10 shadow-sm ring-1 ring-black/5">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#EEA968] border-t-transparent" />
        </div>
      </main>
    );
  }

  if (error || !post) {
    return (
      <main className="min-h-screen bg-[#F7F7FB] px-6 py-16">
        <div className="mx-auto max-w-xl rounded-[28px] bg-white px-8 py-12 text-center shadow-sm ring-1 ring-black/5">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-[#FDF3EC] text-[#EEA968]">
            <MapPin size={28} />
          </div>
          <h1 className="mt-5 text-[22px] font-bold text-gray-900">이동 현황을 확인할 수 없어요</h1>
          <p className="mt-3 text-[14px] leading-relaxed text-gray-500">
            {error ?? "알 수 없는 오류가 발생했습니다."}
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#F7F7FB] px-4 py-6 sm:px-6 sm:py-8">
      <div className="mx-auto max-w-3xl space-y-5">
        <SummaryCard post={post} />
        <StatusCard post={post} liveMessage={liveMessage} />
        <MapSection checkpoints={post.checkpoints} />
        <CheckpointSection checkpoints={post.checkpoints} />
        <TimelineSection post={post} />
      </div>
    </main>
  );
}
