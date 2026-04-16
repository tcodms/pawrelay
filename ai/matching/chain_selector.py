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
    """단일 봉사 구간을 읽기 좋은 텍스트로 포맷한다."""
    vehicle = "차량 있음" if seg.get("vehicle_available") else "차량 없음"
    return (
        f"  • {seg.get('volunteer_name', '봉사자')} "
        f"({seg.get('origin_area', '?')} → {seg.get('destination_area', '?')}, "
        f"{seg.get('available_date', '?')}, {vehicle})"
    )


def _format_chain(index: int, chain: list[dict]) -> str:
    """단일 체인을 번호와 구간 목록으로 포맷한다."""
    segments_text = "\n".join(_format_segment(seg) for seg in chain)
    return f"체인 {index}:\n{segments_text}"


def _build_prompt(chains: list[list[dict]], post: dict) -> str:
    """LLM 체인 선택 프롬프트를 생성한다."""
    chains_text = "\n\n".join(_format_chain(i, c) for i, c in enumerate(chains))
    return f"""유기동물 이동봉사 공고에 대한 릴레이 체인 후보 {len(chains)}개를 검토해주세요.

공고 정보:
- 동물: {post.get("animal_info", "정보 없음")}
- 경로: {post.get("origin", "?")} → {post.get("destination", "?")}
- 이동 날짜: {post.get("scheduled_date", "?")}

체인 후보:
{chains_text}

봉사자 동선의 연속성, 인계 시간 간격, 동물 크기 적합성을 고려해 \
가장 적합한 체인 하나를 선택하고 이유를 한국어 2~3문장으로 설명하세요.

반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트는 포함하지 마세요.
{{
  "selected_chain_index": 선택한 체인 번호(정수),
  "matching_reason": "선택 이유 (한국어 2~3문장)"
}}"""


def _parse_response(text: str) -> dict | None:
    """LLM 응답 JSON을 파싱한다. 형식·타입 오류 시 None 반환."""
    try:
        cleaned = (
            text.strip()
            .removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )
        data = json.loads(cleaned)
        if not isinstance(data, dict):
            logger.warning("응답 타입 오류: dict 아님")
            return None
        if not _REQUIRED_KEYS.issubset(data.keys()):
            logger.warning("응답에 필수 키 누락: %s", data.keys())
            return None
        if not isinstance(data["selected_chain_index"], int):
            logger.warning("selected_chain_index 타입 오류: %r", data["selected_chain_index"])
            return None
        if not isinstance(data["matching_reason"], str) or not data["matching_reason"].strip():
            logger.warning("matching_reason 타입/내용 오류")
            return None
        return data
    except (json.JSONDecodeError, AttributeError) as e:
        logger.warning("JSON 파싱 실패: %s", e)
        return None


async def select_chain(chains: list[list[dict]], post: dict) -> dict:
    """후보 체인 중 최적 체인을 LLM으로 선택한다.

    Args:
        chains: 릴레이 체인 후보 리스트. 각 체인은 봉사 구간 dict 리스트.
        post: 이동봉사 공고 정보 dict.
              필드: animal_info, origin, destination, scheduled_date

    Returns:
        {"selected_chain_index": int, "matching_reason": str}

    Raises:
        ValueError: 최대 재시도 횟수(_MAX_RETRIES=2) 초과 시.
    """
    if not chains or not any(chains):
        raise ValueError("후보 체인이 비어 있습니다.")

    provider = get_llm_provider()
    prompt = _build_prompt(chains, post)
    last_error: Exception | None = None

    for attempt in range(_MAX_RETRIES + 1):
        try:
            response = await provider.complete(prompt)
        except Exception as e:
            last_error = e
            logger.warning(
                "체인 선택 LLM 호출 실패 (시도 %d/%d): %s",
                attempt + 1, _MAX_RETRIES + 1, e,
            )
            continue
        result = _parse_response(response)
        if result is not None:
            if not (0 <= result["selected_chain_index"] < len(chains)):
                logger.warning(
                    "selected_chain_index 범위 오류: %s (chains=%d)",
                    result["selected_chain_index"], len(chains),
                )
                continue
            return result
        logger.warning(
            "체인 선택 파싱 실패 (시도 %d/%d)", attempt + 1, _MAX_RETRIES + 1
        )

    error_msg = f"LLM 체인 선택 실패: {_MAX_RETRIES + 1}회 시도 후 유효한 응답 없음 (post_id={post.get('id')})"
    notify_admin(error_msg)
    if last_error is not None:
        raise ValueError(f"{error_msg} | last_error={last_error}") from last_error
    raise ValueError(error_msg)
