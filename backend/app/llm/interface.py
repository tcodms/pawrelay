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


async def run_matching(post_id: int, candidates: list, post: dict | None = None) -> dict:
    """릴레이 팀 매칭 실행.

    Args:
        post_id: 이동봉사 공고 ID
        candidates: 후보 체인 리스트 (각 체인은 봉사 구간 dict 리스트)
        post: 공고 정보 dict (animal_info, origin, destination, scheduled_date)

    Returns:
        {"selected_chain_index": int, "matching_reason": str}
    """
    from ai.matching.chain_selector import select_chain
    return await select_chain(chains=candidates, post=post or {"id": post_id})


async def detect_anomaly(segment_id: int) -> dict:
    """릴레이 구간 이상 탐지.

    TODO: 구현 필요
    """
    raise NotImplementedError("detect_anomaly는 아직 구현되지 않았습니다.")
