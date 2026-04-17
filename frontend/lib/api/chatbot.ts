/**
 * 챗봇 관련 API 함수
 *
 * api-spec.md 참고:
 *   POST /chatbot/message         메시지 전송 (세션 초기화 포함)
 *   GET  /chatbot/session/{id}    세션 상태 조회 (새로고침 복원)
 *   DELETE /chatbot/session/{id}  세션 삭제
 */
import { request } from "@/lib/api";

export type ChatbotState =
  | "ASK_ORIGIN"
  | "ASK_DESTINATION"
  | "ASK_DATE"
  | "ASK_VEHICLE"
  | "ASK_ANIMAL_SIZE"
  | "CONFIRM"
  | "COMPLETED";

export type InputType = "address_search" | "date_picker" | "buttons" | null;

export interface ChatbotResponse {
  session_id: string;
  state: ChatbotState;
  message: string;
  input_type: InputType;
  options: string[] | null;
  auto_filled: {
    available_date?: string;
    max_animal_size?: string;
    post_origin?: string;
    post_destination?: string;
  } | null;
  completed: boolean;
  schedule_id: number | null;
}

export interface SendMessageRequest {
  session_id: string | null;
  post_id: number | null;
  message: string | null;
}

export async function sendChatbotMessage(
  body: SendMessageRequest
): Promise<ChatbotResponse> {
  return request<ChatbotResponse>("/chatbot/message", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function getChatbotSession(
  sessionId: string
): Promise<ChatbotResponse> {
  return request<ChatbotResponse>(`/chatbot/session/${sessionId}`);
}

export async function deleteChatbotSession(sessionId: string): Promise<void> {
  await request<{ ok: boolean }>(`/chatbot/session/${sessionId}`, {
    method: "DELETE",
  });
}

export const CHATBOT_SESSION_KEY = "chatbot_session_id";
