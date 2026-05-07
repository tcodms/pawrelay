"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import Image from "next/image";
import Script from "next/script";
import {
  ArrowLeft, Clock, Train, Coffee,
  ExternalLink, CheckCircle2, MapPin, Lock, MessageCircle, Navigation,
} from "lucide-react";
import MatchingReasonBubble from "@/components/MatchingReasonBubble";
import { acceptMatching, declineMatching, getSegment } from "@/lib/api/matching";
import { recordCheckpoint, verifyHandover, requestHandover, approveHandover, changeHandoverLocation } from "@/lib/api/relay";
import { ApiError } from "@/lib/api";

declare global {
  interface Window { kakao: any; }
}

// ── 더미 데이터 ───────────────────────────────────────────────────────────────

const DUMMY_SEGMENT = {
  order: 1,
  animal_name: "초코",
  animal_photo_url: "https://images.unsplash.com/photo-1552053831-71594a27632d?w=400",
  animal_size: "small" as const,
  scheduled_date: "2026-04-10",
  pickup_location: { name: "광주광역시 북구", address: "광주광역시 북구 용봉동", lat: 35.1796, lng: 126.9112 },
  dropoff_location: { name: "천안아산역", address: "충남 아산시 배방읍 장재리", lat: 36.7951, lng: 127.1046 },
  scheduled_time: "2026-04-10T09:00:00Z",
  depart_time: "09:00",
  estimated_arrival_time: "10:40",
  status: "proposed",
  notified_at: "2026-04-19T04:00:00Z",
  matching_reason:
    "출발지(광주광역시 북구)가 공고 출발지와 일치하고, 차량이 있어 소형 동물 수송에 최적입니다. 천안아산역에서 다음 봉사자와 인계가 원활하게 이루어질 수 있어 이 구간을 추천드려요.",
  handover_code: null as string | null,
  partner: { name: "이릴레이", phone: "010-1234-5678" },
  kakao_openchat_url: "https://open.kakao.com/o/dummy",
  kakao_map_url: "https://map.kakao.com/link/from/광주광역시 북구,35.1796,126.9112/to/천안아산역,36.7951,127.1046",
  waypoints: {
    train: [
      { id: 1, name: "천안아산역", address: "충남 아산시 배방읍 장재리", distance_km: 0.3, lat: 36.7951, lng: 127.1046 },
      { id: 2, name: "천안역", address: "충남 천안시 동남구 대흥동", distance_km: 4.2, lat: 36.8073, lng: 127.1520 },
    ],
    rest_area: [
      { id: 3, name: "목천휴게소", address: "충남 천안시 동남구 목천읍", distance_km: 8.5, lat: 36.7150, lng: 127.1456 },
    ],
  },
  chain_segments: [
    { volunteer: "나", from: "광주광역시 북구", to: "천안아산역", is_me: true },
    { volunteer: "이릴레이", from: "천안아산역", to: "서울 마포구", is_me: false },
  ],
};

const DUMMY_CONFIRMED_SEGMENT = {
  ...DUMMY_SEGMENT,
  status: "confirmed",
  handover_code: "483920" as string | null,
};

const SIZE_LABEL: Record<string, string> = { small: "소형", medium: "중형", large: "대형" };
const WAYPOINT_ICONS = { train: Train, rest_area: Coffee } as const;
const WAYPOINT_LABELS = { train: "기차역", rest_area: "휴게소" };
type WaypointType = "train" | "rest_area";

// ── 카카오맵 ──────────────────────────────────────────────────────────────────

interface LatLng { lat: number; lng: number; name: string; }

function KakaoMap({ pickup, dropoff, waypointList }: { pickup: LatLng; dropoff: LatLng; waypointList: LatLng[] }) {
  const mapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!mapRef.current || !window.kakao?.maps) return;
    const { maps } = window.kakao;
    const pickupPos  = new maps.LatLng(pickup.lat,  pickup.lng);
    const dropoffPos = new maps.LatLng(dropoff.lat, dropoff.lng);
    const map = new maps.Map(mapRef.current, {
      center: new maps.LatLng((pickup.lat + dropoff.lat) / 2, (pickup.lng + dropoff.lng) / 2),
      level: 10,
    });
    map.addControl(new maps.ZoomControl(), maps.ControlPosition.RIGHT);
    const bounds = new maps.LatLngBounds();
    new maps.Polyline({ path: [pickupPos, dropoffPos], strokeWeight: 3, strokeColor: "#EEA968", strokeOpacity: 0.9, strokeStyle: "solid", map });
    new maps.CustomOverlay({ position: pickupPos,  content: '<div style="width:16px;height:16px;border-radius:50%;background:#EEA968;border:3px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.3)"></div>', xAnchor: 0.5, yAnchor: 0.5, map, zIndex: 4 });
    bounds.extend(pickupPos);
    new maps.CustomOverlay({ position: dropoffPos, content: '<div style="width:16px;height:16px;border-radius:50%;background:white;border:3px solid #EEA968;box-shadow:0 2px 6px rgba(0,0,0,0.3)"></div>', xAnchor: 0.5, yAnchor: 0.5, map, zIndex: 4 });
    bounds.extend(dropoffPos);
    waypointList.forEach((wp) => {
      const pos = new maps.LatLng(wp.lat, wp.lng);
      new maps.CustomOverlay({ position: pos, content: '<div style="width:10px;height:10px;border-radius:50%;background:#D1D5DB;border:2px solid white;box-shadow:0 1px 3px rgba(0,0,0,0.2)"></div>', xAnchor: 0.5, yAnchor: 0.5, map, zIndex: 3 });
      bounds.extend(pos);
    });
    map.setBounds(bounds);
  }, [pickup, dropoff, waypointList]);

  return <div ref={mapRef} className="w-full h-[220px]" />;
}

function MapCard({ mapReady, pickup, dropoff, waypointList, kakaoMapUrl }: {
  mapReady: boolean; pickup: LatLng; dropoff: LatLng; waypointList: LatLng[]; kakaoMapUrl: string;
}) {
  return (
    <div className="rounded-2xl bg-white border border-gray-100 shadow-sm overflow-hidden">
      <div className="relative w-full h-[220px] bg-gray-100">
        {mapReady ? (
          <KakaoMap pickup={pickup} dropoff={dropoff} waypointList={waypointList} />
        ) : (
          <div className="flex h-full items-center justify-center">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-[#EEA968] border-t-transparent" />
          </div>
        )}
        {mapReady && (
          <div className="pointer-events-none absolute bottom-3 left-3 flex flex-col gap-1">
            <div className="flex items-center gap-1.5 rounded-full bg-white/90 px-2.5 py-1 shadow-sm backdrop-blur-sm">
              <div className="h-2.5 w-2.5 rounded-full bg-[#EEA968] shrink-0" />
              <span className="text-[11px] font-semibold text-gray-700">{pickup.name}</span>
            </div>
            <div className="flex items-center gap-1.5 rounded-full bg-white/90 px-2.5 py-1 shadow-sm backdrop-blur-sm">
              <div className="h-2.5 w-2.5 rounded-full border-2 border-[#EEA968] bg-white shrink-0" />
              <span className="text-[11px] font-semibold text-gray-700">{dropoff.name}</span>
            </div>
          </div>
        )}
      </div>
      <a href={kakaoMapUrl} target="_blank" rel="noopener noreferrer"
        className="flex items-center justify-between px-4 py-3 border-t border-gray-50 active:bg-gray-50 transition-colors">
        <div className="flex items-center gap-2">
          <MapPin size={13} className="text-[#EEA968]" />
          <span className="text-[13px] font-semibold text-gray-700">카카오맵으로 경로 보기</span>
        </div>
        <ExternalLink size={13} className="text-gray-400" />
      </a>
    </div>
  );
}

// ── 카운트다운 (수락 기한) ────────────────────────────────────────────────────

function useCountdown(notifiedAt: string, limitHours = 24) {
  const calc = useCallback(() => {
    const deadline  = new Date(notifiedAt).getTime() + limitHours * 60 * 60 * 1000;
    const remaining = Math.max(0, deadline - Date.now());
    return {
      hours:   Math.floor(remaining / (1000 * 60 * 60)),
      minutes: Math.floor((remaining % (1000 * 60 * 60)) / (1000 * 60)),
      seconds: Math.floor((remaining % (1000 * 60)) / 1000),
      expired: remaining === 0,
    };
  }, [notifiedAt, limitHours]);

  const [time, setTime] = useState(calc);
  useEffect(() => { const id = setInterval(() => setTime(calc()), 1000); return () => clearInterval(id); }, [calc]);
  return time;
}

function DeadlineBanner({ notifiedAt }: { notifiedAt: string }) {
  const { hours, minutes, seconds, expired } = useCountdown(notifiedAt);
  const isUrgent = hours < 3;

  if (expired) {
    return (
      <div className="rounded-2xl bg-red-50 shadow-sm px-4 py-3 flex items-center gap-2.5">
        <div className="h-2 w-2 rounded-full bg-red-400 shrink-0" />
        <p className="text-[13px] font-semibold text-red-500">수락 기한이 만료됐어요</p>
      </div>
    );
  }

  return (
    <div className={`rounded-2xl shadow-sm px-4 py-3 flex items-center justify-between ${isUrgent ? "bg-red-50" : "bg-orange-50"}`}>
      <div className="flex items-center gap-2">
        <div className={`h-2 w-2 rounded-full animate-pulse shrink-0 ${isUrgent ? "bg-red-400" : "bg-orange-400"}`} />
        <p className={`text-[13px] font-semibold ${isUrgent ? "text-red-600" : "text-orange-500"}`}>수락 기한</p>
      </div>
      <div className="flex items-center gap-1">
        {[{ value: hours, unit: "시간" }, { value: minutes, unit: "분" }, { value: seconds, unit: "초" }].map(({ value, unit }) => (
          <div key={unit} className="flex items-baseline gap-0.5">
            <span className={`text-[18px] font-bold tabular-nums ${isUrgent ? "text-red-600" : "text-orange-500"}`}>
              {String(value).padStart(2, "0")}
            </span>
            <span className={`text-[11px] ${isUrgent ? "text-red-400" : "text-orange-500/70"}`}>{unit}</span>
            {unit !== "초" && <span className={`text-[14px] font-bold mx-0.5 ${isUrgent ? "text-red-300" : "text-orange-500/40"}`}>:</span>}
          </div>
        ))}
      </div>
    </div>
  );
}

// ── 배너들 ────────────────────────────────────────────────────────────────────

function ConfirmedBanner({ partnerName }: { partnerName: string }) {
  return (
    <div className="rounded-2xl bg-green-50 shadow-sm px-4 py-3.5 flex items-center gap-3">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-green-100">
        <CheckCircle2 size={18} className="text-green-500" />
      </div>
      <div>
        <p className="text-[14px] font-bold text-green-700">매칭이 확정됐어요!</p>
        <p className="text-[12px] text-green-600 mt-0.5">
          파트너 <span className="font-semibold">{partnerName}</span>님과 오픈채팅으로 인계 장소를 협의하세요
        </p>
      </div>
    </div>
  );
}

function InProgressBanner() {
  return (
    <div className="rounded-2xl bg-blue-50 shadow-sm px-4 py-3.5 flex items-center gap-3">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-blue-100">
        <Navigation size={18} className="text-blue-500" />
      </div>
      <div>
        <p className="text-[14px] font-bold text-blue-700">봉사가 시작됐어요!</p>
        <p className="text-[12px] text-blue-600 mt-0.5">각 구간마다 체크포인트를 기록해 주세요</p>
      </div>
    </div>
  );
}

function CompletedBanner({ animalName }: { animalName: string }) {
  return (
    <div className="rounded-2xl bg-[#F0FDF4] border border-green-100 shadow-sm px-4 py-4 flex items-center gap-3">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-green-100">
        <CheckCircle2 size={20} className="text-green-500" />
      </div>
      <div>
        <p className="text-[14px] font-bold text-green-700">봉사가 완료됐어요!</p>
        <p className="text-[12px] text-green-600 mt-0.5">{animalName}와 함께한 릴레이가 완료됐어요. 감사합니다 🐾</p>
      </div>
    </div>
  );
}

// ── 상태 뱃지 ─────────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { label: string; className: string }> = {
    proposed:    { label: "수락 대기 중", className: "bg-orange-50 text-orange-500" },
    pending:     { label: "수락 대기 중", className: "bg-orange-50 text-orange-500" },
    accepted:    { label: "수락 완료",    className: "bg-green-50 text-green-600" },
    confirmed:   { label: "매칭 확정",    className: "bg-green-50 text-green-600" },
    in_progress: { label: "이동 중",      className: "bg-blue-50 text-blue-600" },
    in_transit:  { label: "이동 중",      className: "bg-blue-50 text-blue-600" },
    completed:   { label: "완료",         className: "bg-gray-100 text-gray-500" },
    declined:    { label: "거절됨",       className: "bg-red-50 text-red-400" },
    no_show:     { label: "거절됨",       className: "bg-red-50 text-red-400" },
  };
  const { label, className } = config[status] ?? { label: status, className: "bg-gray-100 text-gray-500" };
  return (
    <span className={`inline-flex items-center rounded-full px-3 py-1 text-[12px] font-semibold ${className}`}>
      {label}
    </span>
  );
}

// ── 인계 코드 ─────────────────────────────────────────────────────────────────

function HandoverCodeCard({ code }: { code: string }) {
  return (
    <div className="rounded-2xl bg-white border border-gray-100 shadow-sm overflow-hidden">
      <div className="bg-[#A07050] px-4 py-2.5 flex items-center gap-2">
        <CheckCircle2 size={14} className="text-white" />
        <p className="text-[12px] font-bold text-white">인계 코드</p>
      </div>
      <div className="px-4 pt-4 flex gap-1.5 justify-center">
        {code.split("").map((c, i) => (
          <div key={i} className="flex-1 max-w-[44px] h-12 rounded-xl bg-gray-50 border border-gray-100 flex items-center justify-center text-[20px] font-bold text-[#EEA968]">
            {c}
          </div>
        ))}
      </div>
      <div className="flex flex-col items-center gap-2 px-4 py-4">
        <Image
          src={`https://api.qrserver.com/v1/create-qr-code/?size=140x140&data=${code}&bgcolor=ffffff&color=1f2937&margin=8`}
          alt={`인계 코드 QR: ${code}`}
          width={140}
          height={140}
          className="rounded-xl"
        />
        <p className="text-[11px] text-gray-400">QR 코드를 스캔하거나 코드를 직접 입력하세요</p>
      </div>
    </div>
  );
}

function HandoverCodeLockedCard({ scheduledDate }: { scheduledDate: string }) {
  const rawDiffDays = Math.ceil(
    (new Date(scheduledDate).getTime() - Date.now()) / (1000 * 60 * 60 * 24)
  );
  const daysUntil = Math.max(0, rawDiffDays);
  const isScheduledInPast = new Date(scheduledDate).getTime() < Date.now();

  return (
    <div className="rounded-2xl bg-white border border-gray-100 shadow-sm overflow-hidden">
      <div className="bg-gray-400 px-4 py-2.5 flex items-center gap-2">
        <Lock size={14} className="text-white" />
        <p className="text-[12px] font-bold text-white">인계 코드</p>
      </div>
      <div className="px-4 py-5 flex flex-col items-center gap-2">
        <div className="flex gap-1.5">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="flex-1 w-10 h-12 rounded-xl bg-gray-100 flex items-center justify-center">
              <Lock size={14} className="text-gray-300" />
            </div>
          ))}
        </div>
        <p className="text-[12px] text-gray-400 mt-1">
          {isScheduledInPast
            ? "이미 공개되었습니다"
            : daysUntil > 0
              ? `출발 ${daysUntil}일 전 · 당일 00:00에 공개돼요`
              : "당일 00:00에 공개돼요"}
        </p>
      </div>
    </div>
  );
}


// ── 인계 코드 입력 카드 ───────────────────────────────────────────────────────

function HandoverInputCard({
  segmentId,
  onComplete,
  isLast = false,
}: {
  segmentId: number;
  onComplete: () => void;
  isLast?: boolean;
}) {
  const [digits, setDigits]           = useState(["", "", "", "", "", ""]);
  const [verifyLoading, setVerifyLoading] = useState(false);
  const [verifyMsg, setVerifyMsg]     = useState<{ text: string; ok: boolean } | null>(null);
  const [showFallback, setShowFallback] = useState(false);
  const [fallbackLoading, setFallbackLoading] = useState(false);
  const [requestSent, setRequestSent] = useState(false);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  const code = digits.join("");

  function handleDigitChange(idx: number, val: string) {
    const num = val.replace(/\D/g, "").slice(-1);
    const next = [...digits];
    next[idx] = num;
    setDigits(next);
    setVerifyMsg(null);
    if (num && idx < 5) inputRefs.current[idx + 1]?.focus();
  }

  function handleKeyDown(idx: number, e: React.KeyboardEvent) {
    if (e.key === "Backspace" && !digits[idx] && idx > 0) {
      inputRefs.current[idx - 1]?.focus();
    }
  }

  async function handleVerify() {
    if (code.length < 6) return;
    setVerifyLoading(true);
    setVerifyMsg(null);
    try {
      const res = await verifyHandover(segmentId, code);
      if (res.status === "completed") {
        onComplete();
      } else {
        setVerifyMsg({ text: "코드 확인 완료! 파트너 입력을 기다리는 중이에요.", ok: true });
      }
    } catch (err) {
      const msg = err instanceof ApiError && err.status === 429
        ? "시도 횟수를 초과했어요. 잠시 후 다시 시도해 주세요."
        : "코드가 일치하지 않아요. 다시 확인해 주세요.";
      setVerifyMsg({ text: msg, ok: false });
    } finally {
      setVerifyLoading(false);
    }
  }

  async function handleRequest() {
    setFallbackLoading(true);
    try {
      await requestHandover(segmentId);
      setRequestSent(true);
    } catch {
      setVerifyMsg({ text: "요청 전송에 실패했어요. 다시 시도해 주세요.", ok: false });
    } finally {
      setFallbackLoading(false);
    }
  }

  async function handleApprove() {
    setFallbackLoading(true);
    try {
      await approveHandover(segmentId);
      onComplete();
    } catch {
      setVerifyMsg({ text: "승인에 실패했어요. 다시 시도해 주세요.", ok: false });
    } finally {
      setFallbackLoading(false);
    }
  }

  return (
    <div className="rounded-2xl bg-white border border-gray-100 shadow-sm px-4 py-4 space-y-4">
      <p className="text-[13px] font-bold text-gray-700">인계 코드 확인</p>

      <div className="flex gap-2 justify-center">
        {digits.map((d, i) => (
          <input
            key={i}
            ref={(el) => { inputRefs.current[i] = el; }}
            type="tel"
            inputMode="numeric"
            maxLength={1}
            value={d}
            onChange={(e) => handleDigitChange(i, e.target.value)}
            onKeyDown={(e) => handleKeyDown(i, e)}
            className={`w-10 h-12 text-center text-[20px] font-bold rounded-xl border-2 focus:outline-none transition-colors ${
              d ? "border-[#EEA968] text-[#EEA968]" : "border-gray-200 text-gray-700"
            }`}
          />
        ))}
      </div>

      {verifyMsg && (
        <p className={`text-[11px] text-center ${verifyMsg.ok ? "text-green-500" : "text-red-400"}`}>
          {verifyMsg.text}
        </p>
      )}

      <button
        onClick={handleVerify}
        disabled={code.length < 6 || verifyLoading}
        className="w-full h-11 rounded-2xl bg-[#EEA968] text-[14px] font-bold text-white disabled:opacity-40 active:scale-[0.97] transition-all"
      >
        {verifyLoading ? (
          <span className="flex items-center justify-center gap-2">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
            확인 중...
          </span>
        ) : "인계 완료 확인"}
      </button>

      <button
        onClick={() => setShowFallback((v) => !v)}
        className="w-full text-center text-[12px] text-gray-400 hover:text-gray-600 transition-colors"
      >
        코드를 입력할 수 없나요?
      </button>

      {showFallback && (
        <div className="space-y-2 border-t border-gray-100 pt-3">
          <p className="text-[11px] text-gray-400 text-center">코드 없이 인계를 완료할 수 있어요</p>
          {!isLast && (
            requestSent ? (
              <div className="flex items-center justify-center gap-1.5 rounded-xl bg-green-50 py-2.5">
                <CheckCircle2 size={13} className="text-green-500" />
                <p className="text-[12px] font-semibold text-green-600">파트너에게 요청을 보냈어요</p>
              </div>
            ) : (
              <button
                onClick={handleRequest}
                disabled={fallbackLoading}
                className="w-full h-10 rounded-xl bg-gray-100 text-[13px] font-semibold text-gray-600 disabled:opacity-40 active:scale-[0.97] transition-all"
              >
                인계 완료 요청 보내기
              </button>
            )
          )}
          {isLast && (
            <button
              onClick={handleApprove}
              disabled={fallbackLoading}
              className="w-full h-10 rounded-xl border border-gray-200 text-[13px] font-semibold text-gray-500 disabled:opacity-40 active:scale-[0.97] transition-all"
            >
              파트너 요청 승인하기
            </button>
          )}
        </div>
      )}
    </div>
  );
}

// ── 인계 위치 변경 모달 ───────────────────────────────────────────────────────

type WaypointEntry = { id: number; name: string; address: string; distance_km: number; lat: number; lng: number };

function HandoverLocationModal({
  waypoints,
  currentName,
  onSelect,
  onClose,
  loading,
}: {
  waypoints: { train: WaypointEntry[]; rest_area: WaypointEntry[] };
  currentName: string;
  onSelect: (id: number, name: string, address: string, lat: number, lng: number) => void;
  onClose: () => void;
  loading: boolean;
}) {
  const sections: { key: keyof typeof waypoints; label: string; Icon: typeof Train }[] = [
    { key: "train",     label: "기차역", Icon: Train  },
    { key: "rest_area", label: "휴게소", Icon: Coffee },
  ];

  return (
    <div className="fixed inset-0 z-[60] flex items-end">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative w-full bg-white rounded-t-3xl px-5 pt-5 max-w-2xl mx-auto"
        style={{ paddingBottom: "calc(2rem + env(safe-area-inset-bottom))" }}>
        <div className="w-10 h-1 rounded-full bg-gray-200 mx-auto mb-4" />
        <p className="text-[16px] font-bold text-gray-800 mb-1">인계 장소 변경</p>
        <p className="text-[12px] text-gray-400 mb-4">현재: <span className="font-semibold text-gray-600">{currentName}</span></p>
        <div className="space-y-4 max-h-[55vh] overflow-y-auto pb-2">
          {sections.map(({ key, label, Icon }) => {
            const items = waypoints[key];
            if (!items.length) return null;
            return (
              <div key={key}>
                <div className="flex items-center gap-1.5 mb-2">
                  <Icon size={12} className="text-gray-400" />
                  <p className="text-[11px] font-semibold text-gray-400 uppercase tracking-wide">{label}</p>
                </div>
                <div className="space-y-1.5">
                  {items.map((wp) => {
                    const isSelected = currentName === wp.name;
                    return (
                      <button
                        key={wp.id}
                        onClick={() => !isSelected && onSelect(wp.id, wp.name, wp.address, wp.lat, wp.lng)}
                        disabled={loading || isSelected}
                        className={`w-full flex items-center justify-between rounded-2xl px-3.5 py-3 text-left transition-all active:scale-[0.98] ${
                          isSelected
                            ? "bg-[#FDF3EC] border-2 border-[#EEA968]"
                            : "bg-gray-50 border border-gray-100 hover:border-gray-200"
                        }`}
                      >
                        <div className="min-w-0">
                          <p className={`text-[13px] font-semibold truncate ${isSelected ? "text-[#C87941]" : "text-gray-700"}`}>
                            {wp.name}
                          </p>
                          <p className="text-[11px] text-gray-400 mt-0.5">{wp.distance_km}km · {wp.address}</p>
                        </div>
                        {isSelected
                          ? <CheckCircle2 size={15} className="text-[#EEA968] shrink-0 ml-2" />
                          : loading
                            ? <span className="h-4 w-4 animate-spin rounded-full border-2 border-[#EEA968] border-t-transparent shrink-0 ml-2" />
                            : null
                        }
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ── 페이지 ────────────────────────────────────────────────────────────────────

export default function MatchingDetailPage() {
  const router  = useRouter();
  const params  = useParams();

  const [mounted, setMounted]                   = useState(false);
  const [status, setStatus]                     = useState(DUMMY_SEGMENT.status);
  const [seg, setSeg]                           = useState(DUMMY_SEGMENT);
  const [acting, setActing]                     = useState(false);
  const [declineInput, setDeclineInput]         = useState("");
  const [showDeclineModal, setShowDeclineModal] = useState(false);
  const [mapReady, setMapReady]                 = useState(false);
  const [departureLoading, setDepartureLoading] = useState(false);
  const [waypointLoading, setWaypointLoading]   = useState(false);
  const [arrivalLoading, setArrivalLoading]     = useState(false);
  const [gpsWarning, setGpsWarning]             = useState(false);
  const [showLocationModal, setShowLocationModal] = useState(false);
  const [locationChanging, setLocationChanging]   = useState(false);

  useEffect(() => {
    const segmentId = Number(params.segment_id);

    getSegment(segmentId)
      .then(({ segment }) => {
        setSeg((prev) => ({
          ...prev,
          order: segment.order,
          animal_name: segment.animal_name || prev.animal_name,
          animal_photo_url: segment.animal_photo_url ?? prev.animal_photo_url,
          animal_size: segment.animal_size || prev.animal_size,
          scheduled_date: segment.scheduled_date || prev.scheduled_date,
          pickup_location: { ...prev.pickup_location, ...segment.pickup_location },
          dropoff_location: { ...prev.dropoff_location, ...segment.dropoff_location },
          scheduled_time: segment.scheduled_time,
          depart_time: segment.depart_time || prev.depart_time,
          estimated_arrival_time: segment.estimated_arrival_time || prev.estimated_arrival_time,
          handover_code: segment.handover_code,
          matching_reason: segment.matching_reason || prev.matching_reason,
          notified_at: segment.notified_at || prev.notified_at,
          partner: segment.partner,
          kakao_openchat_url: segment.kakao_openchat_url,
          ...(segment.chain_segments?.length ? { chain_segments: segment.chain_segments } : {}),
        }));
        setStatus(segment.status);
      })
      .catch(() => {
        const fallback = segmentId === 42 ? DUMMY_CONFIRMED_SEGMENT : DUMMY_SEGMENT;
        setSeg(fallback);
        setStatus(fallback.status);
      })
      .finally(() => setMounted(true));
  }, [params.segment_id]);

  useEffect(() => {
    if (window.kakao?.maps) window.kakao.maps.load(() => setMapReady(true));
  }, []);

  const isProposed   = status === "proposed" || status === "pending";
  const isAccepted   = status === "accepted";
  const isConfirmed  = status === "confirmed";
  const isInProgress = status === "in_progress" || status === "in_transit";
  const isCompleted  = status === "completed";
  const isDeclined   = status === "declined" || status === "no_show";

  const chainSegs = (seg as typeof DUMMY_SEGMENT & { chain_segments?: { is_me: boolean }[] }).chain_segments ?? [];
  const isLast = chainSegs.length === 0 || chainSegs[chainSegs.length - 1]?.is_me === true;

  const todayStr = new Date().toLocaleDateString("sv"); // YYYY-MM-DD (local time)
  const isScheduledToday = seg.scheduled_date === todayStr;

  const allWaypoints: LatLng[] = [
    ...seg.waypoints.train,
    ...seg.waypoints.rest_area,
  ].map((w) => ({ lat: w.lat, lng: w.lng, name: w.name }));

  const segmentId = Number(params.segment_id);

  function goBackToChat(action?: "accepted" | "declined") {
    const chatSession = sessionStorage.getItem("matchingChatSession");
    if (action) sessionStorage.setItem("matchingAction", action);
    sessionStorage.removeItem("matchingChatSession");
    if (chatSession) {
      router.push(`/volunteer/chat/${chatSession}`);
    } else {
      router.back();
    }
  }

  async function getGPS() {
    return new Promise<{ latitude: number | null; longitude: number | null }>((resolve) => {
      if (!navigator.geolocation) { setGpsWarning(true); return resolve({ latitude: null, longitude: null }); }
      navigator.geolocation.getCurrentPosition(
        (pos) => resolve({ latitude: pos.coords.latitude, longitude: pos.coords.longitude }),
        () => { setGpsWarning(true); resolve({ latitude: null, longitude: null }); },
        { timeout: 5000 },
      );
    });
  }

  // API가 좌표를 반환하지 않으므로 dropoff 주소로 카카오맵 URL 생성
  const kakaoMapUrl = seg.dropoff_location.address
    ? `https://map.kakao.com/?q=${encodeURIComponent(seg.dropoff_location.address)}`
    : (seg as typeof DUMMY_SEGMENT).kakao_map_url;

  async function handleDeparture() {
    setDepartureLoading(true);
    setGpsWarning(false);
    const { latitude, longitude } = await getGPS();
    try {
      await recordCheckpoint(segmentId, "departure", latitude, longitude);
      setStatus("in_progress");
    } catch {
      setStatus("in_progress"); // 백엔드 미연결 테스트용
    } finally {
      setDepartureLoading(false);
    }
  }

  async function handleWaypoint() {
    setWaypointLoading(true);
    setGpsWarning(false);
    const { latitude, longitude } = await getGPS();
    try {
      await recordCheckpoint(segmentId, "waypoint", latitude, longitude);
    } catch {
      // ignore — 백엔드 미연결
    } finally {
      setWaypointLoading(false);
    }
  }

  async function handleArrival() {
    setArrivalLoading(true);
    setGpsWarning(false);
    const { latitude, longitude } = await getGPS();
    try {
      await recordCheckpoint(segmentId, "arrival", latitude, longitude);
      setStatus("completed");
    } catch {
      setStatus("completed"); // 백엔드 미연결 테스트용
    } finally {
      setArrivalLoading(false);
    }
  }

  async function handleAccept() {
    setActing(true);
    try {
      await acceptMatching(segmentId);
      goBackToChat("accepted");
    } catch {
      // ignore
    } finally {
      setActing(false);
    }
  }

  async function handleDecline() {
    setActing(true);
    try {
      await declineMatching(segmentId, declineInput || "일정 변경");
      setShowDeclineModal(false);
      goBackToChat("declined");
    } catch {
      // ignore
    } finally {
      setActing(false);
    }
  }

  async function handleChangeLocation(waypointId: number, name: string, address: string, lat: number, lng: number) {
    setLocationChanging(true);
    try {
      const res = await changeHandoverLocation(segmentId, waypointId);
      setSeg((prev) => ({ ...prev, dropoff_location: { ...prev.dropoff_location, ...res.dropoff_location } }));
    } catch {
      // 백엔드 미연결 시 로컬 업데이트로 대체
      setSeg((prev) => ({ ...prev, dropoff_location: { ...prev.dropoff_location, name, address, lat, lng } }));
    } finally {
      setLocationChanging(false);
      setShowLocationModal(false);
    }
  }

  const pageTitle =
    isInProgress || isCompleted ? "봉사 진행 현황"
    : isAccepted || isConfirmed ? "매칭 확정"
    : "매칭 제안";

  if (!mounted) {
    return (
      <main className="min-h-screen bg-gray-50">
        <header className="sticky top-0 z-10 bg-white border-b border-gray-100">
          <div className="mx-auto max-w-2xl flex items-center gap-3 px-4 py-4">
            <button onClick={() => router.back()}
              className="flex h-9 w-9 items-center justify-center rounded-xl text-gray-500 hover:bg-gray-100 transition-colors">
              <ArrowLeft size={20} />
            </button>
            <div className="flex-1 space-y-1.5">
              <div className="h-4 w-24 rounded bg-gray-200 animate-pulse" />
              <div className="h-3 w-32 rounded bg-gray-100 animate-pulse" />
            </div>
          </div>
        </header>
        <div className="mx-auto max-w-2xl px-4 py-4 space-y-3">
          {[140, 200, 100, 120].map((h, i) => (
            <div key={i} className="rounded-2xl bg-white border border-gray-100 animate-pulse" style={{ height: h }} />
          ))}
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gray-50">

      <Script
        src={`https://dapi.kakao.com/v2/maps/sdk.js?appkey=${process.env.NEXT_PUBLIC_KAKAO_MAP_API_KEY}&autoload=false`}
        strategy="afterInteractive"
        onLoad={() => window.kakao.maps.load(() => setMapReady(true))}
      />

      {/* 헤더 */}
      <header className="sticky top-0 z-10 bg-white border-b border-gray-100">
        <div className="mx-auto max-w-2xl flex items-center gap-3 px-4 py-4">
          <button onClick={() => goBackToChat()}
            className="flex h-9 w-9 items-center justify-center rounded-xl text-gray-500 hover:bg-gray-100 transition-colors">
            <ArrowLeft size={20} />
          </button>
          <div className="flex-1">
            <p className="text-[16px] font-bold text-gray-800 leading-tight">{pageTitle}</p>
            <p className="text-[11px] text-gray-400">{seg.scheduled_date} · 구간 {seg.order}</p>
          </div>
          <StatusBadge status={status} />
        </div>
      </header>

      <div className="mx-auto max-w-2xl px-4 py-4 space-y-3 pb-32">

        {/* 상단 배너 */}
        {isProposed                  && <DeadlineBanner notifiedAt={seg.notified_at} />}
        {(isAccepted || isConfirmed) && <ConfirmedBanner partnerName={seg.partner.name} />}
        {isInProgress                && <InProgressBanner />}
        {isCompleted                 && <CompletedBanner animalName={seg.animal_name} />}

        {/* 동물 + 내 구간 */}
        <div className="rounded-2xl bg-white border border-gray-100 shadow-sm overflow-hidden">
          <div className="flex items-center gap-3 px-4 py-3.5 border-b border-gray-50">
            <div className="relative h-12 w-12 rounded-xl overflow-hidden bg-gray-100 shrink-0">
              <Image src={seg.animal_photo_url} alt={seg.animal_name} fill className="object-cover" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <p className="text-[15px] font-bold text-gray-900">{seg.animal_name}</p>
                <span className="rounded-full bg-gray-100 px-1.5 py-0.5 text-[9px] font-bold text-gray-500">
                  {SIZE_LABEL[seg.animal_size]}
                </span>
              </div>
              <p className="text-[12px] text-gray-400 mt-0.5">{seg.scheduled_date}</p>
            </div>
          </div>
          <div className="px-4 py-3.5">
            <p className="text-[10px] font-bold text-[#EEA968] mb-2">내 담당 구간</p>
            <div className="flex items-start gap-2">
              <div className="flex flex-col items-center pt-1">
                <div className="h-2.5 w-2.5 rounded-full bg-[#EEA968]" />
                <div className="w-px h-6 bg-gray-200 my-0.5" />
                <div className="h-2.5 w-2.5 rounded-full border-2 border-[#EEA968]" />
              </div>
              <div className="flex-1 space-y-2">
                <div>
                  <p className="text-[13px] font-semibold text-gray-800">{seg.pickup_location.name}</p>
                  <p className="text-[11px] text-gray-400">{seg.pickup_location.address}</p>
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <p className="text-[13px] font-semibold text-gray-800">{seg.dropoff_location.name}</p>
                    {(isAccepted || isConfirmed || isInProgress) && !isLast && (
                      <button
                        onClick={() => setShowLocationModal(true)}
                        className="text-[10px] font-semibold text-[#C87941] bg-[#FDF3EC] px-2 py-0.5 rounded-full shrink-0"
                      >
                        변경
                      </button>
                    )}
                  </div>
                  <p className="text-[11px] text-gray-400">{seg.dropoff_location.address}</p>
                </div>
              </div>
              <div className="flex flex-col items-end gap-0.5 shrink-0 pt-0.5">
                <div className="flex items-center gap-1">
                  <Clock size={11} className="text-[#EEA968]" />
                  <span className="text-[12px] font-semibold text-gray-600">{seg.depart_time} 출발</span>
                </div>
                {"estimated_arrival_time" in seg && seg.estimated_arrival_time && (
                  <span className="text-[11px] text-gray-400">{seg.estimated_arrival_time} 도착 예정</span>
                )}
              </div>
            </div>
          </div>
          {(isAccepted || isConfirmed) && (
            <div className="border-t border-gray-50 px-4 py-3.5 space-y-2">
              {!isScheduledToday && (
                <p className="text-[11px] text-gray-400">출발 당일({seg.scheduled_date})에 활성화돼요</p>
              )}
              {gpsWarning && (
                <p className="text-[11px] text-amber-500">위치 정보 없이 기록됩니다</p>
              )}
              <button
                onClick={handleDeparture}
                disabled={departureLoading || !isScheduledToday}
                className="w-full h-11 rounded-2xl bg-[#EEA968] text-[14px] font-bold text-white shadow-md shadow-[#EEA968]/20 disabled:opacity-40 active:scale-[0.97] transition-all"
              >
                {departureLoading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    기록 중...
                  </span>
                ) : "출발 기록"}
              </button>
            </div>
          )}
          {isInProgress && !isLast && (
            <div className="border-t border-gray-50 px-4 py-3.5 space-y-2">
              {gpsWarning && (
                <p className="text-[11px] text-amber-500">위치 정보 없이 기록됩니다</p>
              )}
              <button
                onClick={handleWaypoint}
                disabled={waypointLoading}
                className="w-full h-11 rounded-2xl bg-[#EEA968] text-[14px] font-bold text-white shadow-md shadow-[#EEA968]/20 disabled:opacity-40 active:scale-[0.97] transition-all"
              >
                {waypointLoading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    기록 중...
                  </span>
                ) : "인계장소 도착 기록"}
              </button>
            </div>
          )}
          {isInProgress && isLast && (
            <div className="border-t border-gray-50 px-4 py-3.5 space-y-2">
              {gpsWarning && (
                <p className="text-[11px] text-amber-500">위치 정보 없이 기록됩니다</p>
              )}
              <button
                onClick={handleArrival}
                disabled={arrivalLoading}
                className="w-full h-11 rounded-2xl bg-[#EEA968] text-[14px] font-bold text-white shadow-md shadow-[#EEA968]/20 disabled:opacity-40 active:scale-[0.97] transition-all"
              >
                {arrivalLoading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    기록 중...
                  </span>
                ) : "최종 도착 기록"}
              </button>
            </div>
          )}
          {(isAccepted || isConfirmed || isInProgress) && seg.kakao_openchat_url && (
            <a
              href={seg.kakao_openchat_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between border-t border-gray-50 px-4 py-3.5 active:bg-gray-50 transition-colors"
            >
              <div className="flex items-center gap-2.5">
                <MessageCircle size={16} className="text-gray-400 shrink-0" />
                <p className="text-[13px] font-semibold text-gray-700">카카오 오픈채팅 참여</p>
              </div>
              <ExternalLink size={13} className="text-gray-400 shrink-0" />
            </a>
          )}
        </div>

        {/* 지도 */}
        <MapCard
          mapReady={mapReady}
          pickup={{ lat: seg.pickup_location.lat, lng: seg.pickup_location.lng, name: seg.pickup_location.name }}
          dropoff={{ lat: seg.dropoff_location.lat, lng: seg.dropoff_location.lng, name: seg.dropoff_location.name }}
          waypointList={allWaypoints}
          kakaoMapUrl={kakaoMapUrl}
        />

        {/* 완료 — 릴레이 체인 요약 */}
        {isCompleted && chainSegs.length > 0 && (
          <div className="rounded-2xl bg-white border border-gray-100 shadow-sm px-4 py-4">
            <p className="text-[12px] font-bold text-[#EEA968] mb-3">릴레이 전체 구간</p>
            <div className="space-y-2">
              {chainSegs.map((cs, idx) => (
                <div key={idx} className={`flex items-center gap-3 rounded-xl px-3 py-2.5 ${cs.is_me ? "bg-[#FDF3EC]" : "bg-gray-50"}`}>
                  <div className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[11px] font-bold ${cs.is_me ? "bg-[#EEA968] text-white" : "bg-gray-200 text-gray-500"}`}>
                    {idx + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className={`text-[13px] font-semibold truncate ${cs.is_me ? "text-[#C87941]" : "text-gray-700"}`}>
                      {cs.is_me ? "나" : cs.volunteer}
                    </p>
                    <p className="text-[11px] text-gray-400 truncate">{cs.from} → {cs.to}</p>
                  </div>
                  {cs.is_me && (
                    <CheckCircle2 size={15} className="text-[#EEA968] shrink-0" />
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* AI 매칭 이유 */}
        {!isInProgress && !isCompleted && <MatchingReasonBubble reason={seg.matching_reason} />}

        {/* 인계 코드 */}
        {(isAccepted || isConfirmed || isInProgress) && (
          seg.handover_code
            ? <HandoverCodeCard code={seg.handover_code} />
            : <HandoverCodeLockedCard scheduledDate={seg.scheduled_date} />
        )}

        {/* 인계 코드 입력 */}
        {isInProgress && (
          <HandoverInputCard
            segmentId={segmentId}
            onComplete={() => setStatus("completed")}
            isLast={isLast}
          />
        )}

        {/* 수락/거절 */}
        {isProposed && (
          <div className="flex gap-3">
            <button onClick={handleAccept} disabled={acting}
              className="flex-1 rounded-2xl bg-[#EEA968] text-[15px] font-bold text-white shadow-lg shadow-[#EEA968]/20 active:scale-[0.97] disabled:opacity-40 transition-all py-3.5">
              수락하기
            </button>
            <button onClick={() => setShowDeclineModal(true)} disabled={acting}
              className="flex-1 rounded-2xl border border-gray-200 bg-white text-[15px] font-semibold text-gray-500 active:scale-[0.97] disabled:opacity-40 transition-all py-3.5">
              거절하기
            </button>
          </div>
        )}

        {isDeclined && (
          <div className="flex items-center gap-2.5 rounded-2xl bg-gray-50 border border-gray-100 px-4 py-3.5">
            <p className="text-[13px] text-gray-500">거절 처리가 완료됐어요. 다음 기회에 또 만나요! 🐾</p>
          </div>
        )}
      </div>

      {/* 거절 사유 모달 */}
      {showDeclineModal && (
        <div className="fixed inset-0 z-[60] flex items-end">
          <div className="absolute inset-0 bg-black/40" onClick={() => setShowDeclineModal(false)} />
          <div className="relative w-full bg-white rounded-t-3xl px-5 pt-5 max-w-2xl mx-auto"
            style={{ paddingBottom: "calc(2rem + env(safe-area-inset-bottom))" }}>
            <div className="w-10 h-1 rounded-full bg-gray-200 mx-auto mb-4" />
            <p className="text-[16px] font-bold text-gray-800 mb-1">거절 사유</p>
            <p className="text-[13px] text-gray-400 mb-3">선택 사항이에요</p>
            <textarea
              value={declineInput}
              onChange={(e) => setDeclineInput(e.target.value)}
              placeholder="예) 일정이 변경되었어요"
              rows={3}
              className="w-full rounded-2xl bg-gray-50 border border-gray-100 px-4 py-3 text-[14px] text-gray-800 placeholder:text-gray-400 focus:outline-none resize-none"
            />
            <div className="flex gap-2.5 mt-3">
              <button onClick={() => setShowDeclineModal(false)}
                className="flex-1 h-12 rounded-2xl border border-gray-200 text-[14px] font-semibold text-gray-500">
                취소
              </button>
              <button onClick={handleDecline} disabled={acting}
                className="flex-1 h-12 rounded-2xl bg-red-400 text-[14px] font-bold text-white disabled:opacity-40">
                거절하기
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 인계 위치 변경 모달 */}
      {showLocationModal && (
        <HandoverLocationModal
          waypoints={seg.waypoints}
          currentName={seg.dropoff_location.name}
          onSelect={handleChangeLocation}
          onClose={() => setShowLocationModal(false)}
          loading={locationChanging}
        />
      )}

    </main>
  );
}
