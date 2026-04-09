/**
 * 매칭 관련 API 함수
 *
 * api-spec.md 참고:
 *   POST /matching/accept/{segment_id}   봉사자 매칭 수락
 *   POST /matching/decline/{segment_id}  봉사자 매칭 거절
 *
 * 보호소 측 승인/거절 엔드포인트는 api-spec.md 미확정.
 * → 백엔드 팀에 PATCH /relay-chains/{id}/approve, /reject 추가 요청 필요.
 */
import { request } from "@/lib/api";

// ── 봉사자 매칭 수락/거절 ─────────────────────────────────────────────────────

export async function acceptMatching(segmentId: number): Promise<void> {
  await request<{ ok: boolean }>(`/matching/accept/${segmentId}`, {
    method: "POST",
  });
}

export async function declineMatching(segmentId: number, reason: string): Promise<void> {
  await request<{ status: string }>(`/matching/decline/${segmentId}`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
}

// ── 보호소 매칭 승인/거절 (스펙 미확정) ──────────────────────────────────────

export async function approveShelterMatching(chainId: number): Promise<void> {
  // TODO: 엔드포인트 확정 후 구현
  // await request<{ ok: boolean }>(`/relay-chains/${chainId}/approve`, { method: "PATCH" });
  void chainId;
}

export async function rejectShelterMatching(chainId: number): Promise<void> {
  // TODO: 엔드포인트 확정 후 구현
  // await request<{ ok: boolean }>(`/relay-chains/${chainId}/reject`, { method: "PATCH" });
  void chainId;
}
