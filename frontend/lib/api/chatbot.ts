/**
 * 챗봇 관련 유틸리티
 *
 * 현재: DUMMY_MODE = true (UI 개발용)
 * 백엔드 연동 시: DUMMY_MODE = false 로 변경
 */
import { request } from "@/lib/api";

export const CHATBOT_SESSION_KEY = "chatbot_session_id";
export const CHATBOT_POST_CONTEXT_KEY = "chatbot_post_context";

export interface PostContext {
  post_id: number;
  animal_name?: string;
  photo_url?: string;
  origin?: string;
  destination?: string;
  available_date?: string;
  max_animal_size?: "small" | "medium" | "large";
}

export interface PostSuggestion {
  post_id: number;
  animal_name: string;
  photo_url?: string;
  origin: string;
  destination: string;
  scheduled_date: string;
  max_animal_size: "small" | "medium" | "large";
}

export interface ChatbotApiResponse {
  session_id: string;
  message: string;
  /** 자연어 대화 중에는 null. 위젯 종류에 따라 분기됨 */
  input_type: "buttons" | "date_picker" | "address_search" | null;
  /** input_type: "buttons"일 때만 존재. 예) ["등록하기", "처음부터 다시"] */
  options: string[] | null;
  completed: boolean;
  schedule_id: number | null;
}

// ── 더미 모드 ──────────────────────────────────────────────────────────────────

const DUMMY_MODE = false;

function dummyResponse(
  sessionId: string | null,
  postId: number | null,
  message: string | null
): ChatbotApiResponse {
  const sid = sessionId ?? crypto.randomUUID();
  const base = { session_id: sid, input_type: null as "buttons" | "date_picker" | "address_search" | null, options: null, completed: false, schedule_id: null };

  // 세션 초기화 (인사말)
  if (message === null) {
    return {
      ...base,
      message: postId
        ? "릴레이 봉사를 신청해 주셔서 감사해요! 🐾\n출발 가능한 지역과 차량 유무를 알려주시면 바로 진행할게요."
        : "안녕하세요! 봉사 일정을 알려주세요.\n출발 지역, 날짜, 차량 유무 등 자유롭게 말씀해 주세요.",
    };
  }

  // 확정 버튼 응답 처리
  if (message === "등록하기") {
    return { ...base, message: "봉사 정보가 등록되었어요! 매칭 제안 해드릴게요. 🐾", completed: true, schedule_id: 17 };
  }
  if (message === "수락할게요") {
    return { ...base, message: "수락 완료됐어요! 보호소 최종 확인 후 매칭이 확정돼요. 🐾", completed: true, schedule_id: 17 };
  }
  if (message === "거절할게요") {
    return { ...base, message: "알겠어요. 다른 봉사 기회가 생기면 또 알려드릴게요! 🐾", completed: true };
  }
  if (message === "처음부터 다시") {
    return { ...base, message: "알겠어요. 다시 처음부터 시작해볼게요! 🐾" };
  }

  // 자연어 파싱 (더미용 간이 키워드)
  const hasRegion = /광주|서울|부산|대구|인천|대전|울산|수원|천안|경기|전남|전북/.test(message);

  // 지역 포함 → 차량 질문
  if (hasRegion) {
    return { ...base, message: "알겠어요! 차량이 있으신가요? 없으시면 대중교통 이용도 괜찮아요." };
  }

  // 그 외 모든 답변 → 충분한 정보 수집으로 간주하고 CONFIRM
  return {
    ...base,
    message: "감사합니다! 아래 내용으로 동선을 등록할까요?\n\n입력하신 조건으로 매칭을 시작할게요.",
    input_type: "buttons",
    options: ["등록하기", "처음부터 다시"],
  };
}

// ── API 함수 ──────────────────────────────────────────────────────────────────

/**
 * 챗봇 메시지 전송
 * @param sessionId - 세션 ID (첫 요청 시 null, BE가 생성해서 반환)
 * @param postId    - 게시판에서 진입한 경우의 공고 ID (직접 진입 시 null)
 * @param message   - 사용자 메시지 (세션 초기화 시 null)
 */
export interface AppliedPostInfo {
  animal_name: string;
  animal_size: string;
  animal_photo_url: string | null;
  origin: string;
  destination: string;
  post_status: string;
}

export interface ScheduleItem {
  id: number;
  post_id: number | null;
  origin_area: string;
  destination_area: string;
  available_date: string;
  available_time: string | null;
  max_animal_size: string;
  status: string;
  applied_post: AppliedPostInfo | null;
}

export async function getMySchedules(): Promise<ScheduleItem[]> {
  const res = await request<{ schedules: ScheduleItem[] }>("/volunteers/schedules");
  return res.schedules;
}

export interface ChatSessionListItem {
  session_id: string;
  title: string;
  last_message: string;
  state: string;
  updated_at: string;
}

export async function getChatSessions(): Promise<ChatSessionListItem[]> {
  return request<ChatSessionListItem[]>("/chatbot/sessions");
}

export async function deleteChatSession(sessionId: string): Promise<void> {
  await request<void>(`/chatbot/session/${sessionId}`, { method: "DELETE" });
}

export async function sendChatMessage(
  sessionId: string | null,
  postId: number | null,
  message: string | null
): Promise<ChatbotApiResponse> {
  if (DUMMY_MODE) {
    await new Promise((r) => setTimeout(r, 700));
    return dummyResponse(sessionId, postId, message);
  }

  return request<ChatbotApiResponse>("/chatbot/message", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, post_id: postId, message }),
  });
}
