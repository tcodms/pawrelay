class ChatbotError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(message)


class InvalidInputError(ChatbotError):
    def __init__(self, message="잘못된 입력입니다. 다시 시도해주세요."):
        super().__init__("INVALID_INPUT", message)


class SessionExpiredError(ChatbotError):
    def __init__(self, message="세션이 만료되었습니다. 처음부터 다시 시작해주세요."):
        super().__init__("SESSION_EXPIRED", message)


class GeocodingFailedError(ChatbotError):
    def __init__(self, message="주소를 찾을 수 없습니다. 다시 입력해주세요."):
        super().__init__("GEOCODING_FAILED", message)


class ScheduleSaveFailedError(ChatbotError):
    def __init__(self, message="등록에 실패했습니다. 다시 시도해주세요."):
        super().__init__("SCHEDULE_SAVE_FAILED", message)


class ParseFailedError(ChatbotError):
    def __init__(self, message="입력을 이해하지 못했습니다. 다시 말씀해주세요."):
        super().__init__("PARSE_FAILED", message)


class LLMError(ChatbotError):
    def __init__(self, message="AI 처리 중 오류가 발생했습니다. 다시 시도해주세요."):
        super().__init__("LLM_ERROR", message)