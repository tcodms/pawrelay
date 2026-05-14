import { request } from "@/lib/api";

export type CheckpointType = "departure" | "waypoint" | "arrival";

export interface CheckpointResponse {
  checkpoint_id: number;
  recorded_at: string;
}

export interface HandoverVerifyResponse {
  status: "completed" | "waiting_partner";
}

export interface HandoverLocationResponse {
  dropoff_location: { name: string; address: string };
}

export interface SOSResponse {
  message: string;
}

export async function recordCheckpoint(
  segmentId: number,
  type: CheckpointType,
  latitude: number | null,
  longitude: number | null,
): Promise<CheckpointResponse> {
  return request<CheckpointResponse>("/relay/checkpoint", {
    method: "POST",
    body: JSON.stringify({ segment_id: segmentId, type, latitude, longitude }),
  });
}

export async function verifyHandover(
  segmentId: number,
  code: string,
): Promise<HandoverVerifyResponse> {
  return request<HandoverVerifyResponse>("/relay/handover/verify", {
    method: "POST",
    body: JSON.stringify({ segment_id: segmentId, code }),
  });
}

export async function requestHandover(segmentId: number): Promise<{ ok: boolean }> {
  return request<{ ok: boolean }>(`/relay/handover/request/${segmentId}`, {
    method: "POST",
  });
}

export async function approveHandover(segmentId: number): Promise<{ status: string }> {
  return request<{ status: string }>(`/relay/handover/approve/${segmentId}`, {
    method: "POST",
  });
}

export async function changeHandoverLocation(
  segmentId: number,
  waypointId: number,
): Promise<HandoverLocationResponse> {
  return request<HandoverLocationResponse>(`/relay/segments/${segmentId}/handover-location`, {
    method: "PATCH",
    body: JSON.stringify({ waypoint_id: waypointId }),
  });
}

export async function reportSOS(
  segmentId: number,
  latitude: number | null,
  longitude: number | null,
): Promise<SOSResponse> {
  return request<SOSResponse>("/relay/emergency/sos", {
    method: "POST",
    body: JSON.stringify({ segment_id: segmentId, latitude, longitude }),
  });
}

export async function reportDelay(
  segmentId: number,
  message: string,
): Promise<{ ok: boolean }> {
  return request<{ ok: boolean }>("/relay/emergency/delay", {
    method: "POST",
    body: JSON.stringify({ segment_id: segmentId, message }),
  });
}

export async function confirmPing(segmentId: number): Promise<void> {
  await request<{ ok: boolean }>(`/relay/segments/${segmentId}/ping/confirm`, { method: "POST" });
}
