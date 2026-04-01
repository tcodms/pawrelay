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