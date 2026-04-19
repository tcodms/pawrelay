/**
 * 매칭 관련 API 함수
 *
 * api-spec.md 참고:
 *   POST  /matching/accept/{segment_id}                봉사자 매칭 수락
 *   POST  /matching/decline/{segment_id}               봉사자 매칭 거절
 *   PATCH /matching/relay-chains/{chain_id}/approve    보호소 매칭 승인
 *   PATCH /matching/relay-chains/{chain_id}/reject     보호소 매칭 거절
 */
import { request } from "@/lib/api";

// ── 타입 ──────────────────────────────────────────────────────────────────────

interface WaypointItem {
  name: string;
  address: string;
}

export interface AcceptMatchingResponse {
  segment: {
    order: number;
    pickup_location: { name: string; address: string };
    dropoff_location: { name: string; address: string };
    scheduled_time: string;
    handover_code: string | null;
    partner: { name: string; phone: string };
    kakao_openchat_url: string;
    waypoints: {
      train: WaypointItem[];
      bus: WaypointItem[];
      rest_area: WaypointItem[];
    };
  };
}

// ── 봉사자 매칭 수락/거절 ─────────────────────────────────────────────────────

export async function acceptMatching(segmentId: number): Promise<AcceptMatchingResponse> {
  return request<AcceptMatchingResponse>(`/matching/accept/${segmentId}`, {
    method: "POST",
  });
}

export async function declineMatching(segmentId: number, reason: string): Promise<void> {
  await request<{ status: string }>(`/matching/decline/${segmentId}`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
}

// ── 세그먼트 상세 조회 ────────────────────────────────────────────────────────

export interface SegmentDetail {
  order: number;
  pickup_location: { name: string; address: string };
  dropoff_location: { name: string; address: string };
  scheduled_time: string;
  handover_code: string | null;
  partner: { name: string; phone: string };
  kakao_openchat_url: string;
  status: string;
}

export async function getSegment(segmentId: number): Promise<{ segment: SegmentDetail }> {
  return request<{ segment: SegmentDetail }>(`/matching/segments/${segmentId}`);
}

// ── 보호소 매칭 승인/거절 ─────────────────────────────────────────────────────

export async function approveShelterMatching(chainId: number): Promise<void> {
  await request<{ ok: boolean }>(`/matching/relay-chains/${chainId}/approve`, {
    method: "PATCH",
  });
}

export async function rejectShelterMatching(chainId: number): Promise<void> {
  await request<{ ok: boolean }>(`/matching/relay-chains/${chainId}/reject`, {
    method: "PATCH",
  });
}
