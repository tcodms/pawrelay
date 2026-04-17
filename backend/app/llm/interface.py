"""
백엔드 ↔ AI 인터페이스 계약.

백엔드는 이 파일의 함수만 호출한다. 내부 구현을 직접 수정하지 말 것.
변경 시 팀 전체 협의 필수 (CLAUDE.md 참고).
"""
from ai.chatbot.engine import ChatbotEngine

# user_id → ChatbotEngine 캐시
# TODO: 세션 관리가 완성되면 MockSessionManager → RedisSessionManager로 교체
_engines: dict[int, ChatbotEngine] = {}


async def chat(user_id: int, message: str) -> str:
    """봉사자 챗봇 메시지 처리.

    Args:
        user_id: 봉사자 사용자 ID
        message: 사용자 입력 메시지

    Returns:
        챗봇 응답 메시지 문자열
    """
    if user_id not in _engines:
        _engines[user_id] = ChatbotEngine()

    engine = _engines[user_id]
    result = await engine.process_input(message)
    return result["message"]


_POST_REQUIRED_KEYS = {"animal_info", "origin", "destination", "scheduled_date"}


async def run_matching(post_id: int, candidates: list, post: dict | None = None) -> dict:
    """릴레이 팀 매칭 실행. post 누락 또는 필수 키 없으면 ValueError."""
    if post is None:
        raise ValueError("run_matching 호출 시 post 공고 정보가 필요합니다.")
    missing = _POST_REQUIRED_KEYS - post.keys()
    if missing:
        raise ValueError(f"post에 필수 키 누락: {missing}")
    from ai.matching.chain_selector import select_chain
    return await select_chain(chains=candidates, post=post)


async def detect_anomaly(segment_id: int) -> dict:
    """릴레이 구간 이상 탐지.

    TODO: 구현 필요
    """
    raise NotImplementedError("detect_anomaly는 아직 구현되지 않았습니다.")
