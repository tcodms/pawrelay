"""LLM 기반 릴레이 체인 선택기 (3단계 매칭).

매칭 플로우:
  1단계 SQL + 2단계 Python 검증을 거친 후보 체인을 받아
  LLM이 최적 체인 하나를 선택하고 matching_reason을 한국어로 생성한다.

LLM에게 수학 계산을 시키지 않는다. 체인 시간 검증은 2단계 Python 담당.
"""
import json
import logging

from ai.errors import notify_admin
from ai.providers import get_llm_provider

logger = logging.getLogger(__name__)

_MAX_RETRIES = 2
_REQUIRED_KEYS = {"selected_chain_index", "matching_reason"}


def _format_segment(seg: dict) -> str:
    """단일 봉사 구간을 포맷한다. 봉사자 이름은 PII 보호를 위해 제외."""
    vehicle = "차량 있음" if seg.get("vehicle_available") else "차량 없음"
    return (
        f"  • {seg.get('origin_area', '?')} → {seg.get('destination_area', '?')}, "
        f"{seg.get('available_date', '?')}, {vehicle}"
    )


def _format_chain(index: int, chain: list[dict]) -> str:
    """단일 체인을 번호와 구간 목록으로 포맷한다."""
    segments_text = "\n".join(_format_segment(seg) for seg in chain)
    return f"체인 {index}:\n{segments_text}"


def _build_post_section(post: dict) -> str:
    """프롬프트용 공고 정보 섹션을 생성한다."""
    return (
        f"- 동물: {post.get('animal_info', '정보 없음')}\n"
        f"- 경로: {post.get('origin', '?')} → {post.get('destination', '?')}\n"
        f"- 이동 날짜: {post.get('scheduled_date', '?')}"
    )


def _build_prompt(chains: list[list[dict]], post: dict) -> str:
    """LLM 체인 선택 프롬프트를 생성한다."""
    chains_text = "\n\n".join(_format_chain(i, c) for i, c in enumerate(chains))
    post_info = _build_post_section(post)
    return f"""유기동물 이동봉사 공고에 대한 릴레이 체인 후보 {len(chains)}개를 검토해주세요.

공고 정보:
{post_info}

체인 후보:
{chains_text}

봉사자 동선의 연속성, 인계 시간 간격, 동물 크기 적합성을 고려해 \
가장 적합한 체인 하나를 선택하고 이유를 한국어 2~3문장으로 설명하세요.

반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트는 포함하지 마세요.
{{
  "selected_chain_index": 선택한 체인 번호(정수),
  "matching_reason": "선택 이유 (한국어 2~3문장)"
}}"""


def _validate_fields(data: dict) -> bool:
    """파싱된 dict의 필드 타입·값을 검증한다. 실패 시 False 반환."""
    if not _REQUIRED_KEYS.issubset(data.keys()):
        logger.warning("응답에 필수 키 누락: %s", data.keys())
        return False
    if type(data["selected_chain_index"]) is not int:
        logger.warning("selected_chain_index 타입 오류: %r", data["selected_chain_index"])
        return False
    if not isinstance(data["matching_reason"], str) or not data["matching_reason"].strip():
        logger.warning("matching_reason 타입/내용 오류")
        return False
    sentence_count = len(
        [s for s in data["matching_reason"].replace("。", ".").split(".") if s.strip()]
    )
    if not (2 <= sentence_count <= 3):
        logger.warning("matching_reason 문장 수 오류: %d문장", sentence_count)
        return False
    return True


def _parse_response(text: str) -> dict | None:
    """LLM 응답 JSON을 파싱한다. 형식·타입 오류 시 None 반환."""
    try:
        cleaned = (
            text.strip()
            .removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        )
        data = json.loads(cleaned)
        if not isinstance(data, dict):
            logger.warning("응답 타입 오류: dict 아님")
            return None
        return data if _validate_fields(data) else None
    except (json.JSONDecodeError, AttributeError) as e:
        logger.warning("JSON 파싱 실패: %s", e)
        return None


def _init_provider(post: dict):
    """LLM provider를 초기화한다. 실패 시 관리자 알림 후 ValueError."""
    try:
        return get_llm_provider()
    except Exception as e:
        error_msg = f"LLM provider 초기화 실패 (post_id={post.get('id')}): {e}"
        notify_admin(error_msg)
        raise ValueError(error_msg) from e


async def _attempt_once(provider, prompt: str, chains: list) -> dict | None:
    """LLM 단일 호출 시도. 파싱 실패 또는 범위 오류 시 None 반환."""
    response = await provider.complete(prompt)
    result = _parse_response(response)
    if result is None:
        return None
    if not (0 <= result["selected_chain_index"] < len(chains)):
        logger.warning("selected_chain_index 범위 오류: %s", result["selected_chain_index"])
        return None
    return result


def _handle_all_failed(post: dict, last_error: Exception | None) -> None:
    """모든 재시도 실패 후 관리자 알림 + ValueError 발생."""
    error_msg = (
        f"LLM 체인 선택 실패: {_MAX_RETRIES + 1}회 시도 후 유효한 응답 없음"
        f" (post_id={post.get('id')})"
    )
    notify_admin(error_msg)
    if last_error is not None:
        raise ValueError(f"{error_msg} | last_error={last_error}") from last_error
    raise ValueError(error_msg)


async def select_chain(chains: list[list[dict]], post: dict) -> dict:
    """후보 체인 중 최적 체인을 LLM으로 선택한다."""
    if not chains:
        raise ValueError("후보 체인이 비어 있습니다.")
    if any(not chain for chain in chains):
        raise ValueError("빈 체인이 포함되어 있습니다.")
    provider = _init_provider(post)
    prompt = _build_prompt(chains, post)
    last_error: Exception | None = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            result = await _attempt_once(provider, prompt, chains)
        except Exception as e:
            last_error = e
            logger.warning("LLM 호출 실패 (시도 %d/%d): %s", attempt + 1, _MAX_RETRIES + 1, e)
            continue
        if result is not None:
            return result
        logger.warning("파싱 실패 (시도 %d/%d)", attempt + 1, _MAX_RETRIES + 1)
    _handle_all_failed(post, last_error)
