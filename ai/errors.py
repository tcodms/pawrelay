import logging

_admin_logger = logging.getLogger("admin.alert")


def notify_admin(message: str) -> None:
    """관리자에게 긴급 알림을 보낸다.

    현재는 ERROR 레벨 로깅으로 구현한다.
    TODO: 알림 시스템 구축 후 notifications 테이블 또는 이메일 연동으로 교체.
    """
    _admin_logger.error("[ADMIN ALERT] %s", message)


class ChatbotError(Exception):
    """챗봇 에러 베이스 클래스."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class InvalidInputError(ChatbotError):
    """잘못된 입력 (버튼 state에서 예상 외 입력)."""

    def __init__(self, message="잘못된 입력입니다. 다시 시도해주세요."):
        super().__init__("INVALID_INPUT", message)


class SessionExpiredError(ChatbotError):
    """세션 만료 (1시간 초과)."""

    def __init__(self, message="세션이 만료되었습니다. 처음부터 다시 시작해주세요."):
        super().__init__("SESSION_EXPIRED", message)


class GeocodingFailedError(ChatbotError):
    """주소 좌표 변환 실패."""

    def __init__(self, message="주소를 찾을 수 없습니다. 다시 입력해주세요."):
        super().__init__("GEOCODING_FAILED", message)


class ScheduleSaveFailedError(ChatbotError):
    """volunteer_schedules 저장 실패."""

    def __init__(self, message="등록에 실패했습니다. 다시 시도해주세요."):
        super().__init__("SCHEDULE_SAVE_FAILED", message)


class ParseFailedError(ChatbotError):
    """LLM 응답 파싱 실패."""

    def __init__(self, message="입력을 이해하지 못했습니다. 다시 말씀해주세요."):
        super().__init__("PARSE_FAILED", message)


class LLMError(ChatbotError):
    """LLM API 호출 실패."""

    def __init__(self, message="AI 처리 중 오류가 발생했습니다. 다시 시도해주세요."):
        super().__init__("LLM_ERROR", message)