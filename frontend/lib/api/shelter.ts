/**
 * 보호소 프로필 API 함수
 *
 * GET /shelters/me 엔드포인트는 api-spec.md 미확정.
 * → 백엔드 팀에 추가 요청 필요.
 */
import { request } from "@/lib/api";

export interface ShelterProfile {
  id: number;
  name: string;
  email: string;
  verified_at: string | null;
}

export async function getShelterProfile(): Promise<ShelterProfile> {
  // TODO: return request<ShelterProfile>("/shelters/me");
  // 스펙 미확정 — 임시 더미 반환
  void request; // 연동 시 삭제
  return { id: 0, name: "행복 동물 보호소", email: "", verified_at: null };
}
