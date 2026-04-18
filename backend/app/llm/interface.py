from ai.chatbot.engine import ChatbotEngine

# user_id → ChatbotEngine 캐시
# TODO: 세션 관리가 완성되면 MockSessionManager → RedisSessionManager로 교체
_engines: dict[int, ChatbotEngine] = {}


async def chat(user_id: int, message: str) -> str:
    if user_id not in _engines:
        _engines[user_id] = ChatbotEngine()

    engine = _engines[user_id]
    result = await engine.process_input(message)
    return result["message"]


_POST_REQUIRED_KEYS = {"animal_info", "origin", "destination", "scheduled_date"}


async def run_matching(post_id: int, candidates: list, post: dict | None = None) -> dict:
    if post is None:
        raise ValueError("run_matching 호출 시 post 공고 정보가 필요합니다.")
    missing = _POST_REQUIRED_KEYS - post.keys()
    if missing:
        raise ValueError(f"post에 필수 키 누락: {missing}")
    from ai.matching.chain_selector import select_chain
    return await select_chain(chains=candidates, post=post)


async def detect_anomaly(segment_id: int) -> dict:
    raise NotImplementedError("detect_anomaly는 아직 구현되지 않았습니다.")
