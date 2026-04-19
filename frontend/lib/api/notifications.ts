import { request } from "@/lib/api";

export interface AppNotification {
  id: number;
  type: string;
  message: string;
  payload: { segment_id?: number; url?: string; chat_session_id?: string };
  created_at: string;
}

export async function getUnreadNotifications(): Promise<AppNotification[]> {
  const res = await request<{ notifications: AppNotification[] }>("/notifications/unread");
  return res.notifications;
}

export async function markNotificationRead(id: number): Promise<void> {
  await request<{ ok: boolean }>(`/notifications/${id}/read`, { method: "PATCH" });
}
