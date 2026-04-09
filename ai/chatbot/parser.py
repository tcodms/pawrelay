import json
from typing import Optional

from pydantic import BaseModel, field_validator


REQUIRED_FIELDS = [
    "origin",
    "destination",
    "available_date",
    "vehicle_available",
    "max_animal_size",
]

OPTIONAL_FIELDS = [
    "available_time",
    "waypoint",
]

ALL_FIELDS = REQUIRED_FIELDS + OPTIONAL_FIELDS

ANIMAL_SIZE_DISPLAY = {
    "small": "소형 (5kg 이하)",
    "medium": "중형 (5~15kg)",
    "large": "대형 (15kg 이상)",
}

VEHICLE_DISPLAY = {
    True: "있음",
    False: "없음",
}


class _LLMResponseSchema(BaseModel):
    """LLM 응답 스키마. 허용되지 않은 필드는 무시한다."""
    extracted: dict
    next_question: Optional[str] = None
    all_complete: bool = False

    @field_validator("extracted")
    @classmethod
    def filter_extracted_fields(cls, v: dict) -> dict:
        """허용된 필드만 남기고 나머지는 제거한다."""
        return {k: val for k, val in v.items() if k in ALL_FIELDS}


def parse_llm_response(response_text: str) -> Optional[dict]:
    """LLM 응답 JSON을 파싱하고 Pydantic으로 검증한다.

    Returns:
        dict: {extracted, next_question, all_complete}
        None: 파싱 또는 검증 실패
    """
    try:
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
        raw = json.loads(cleaned)
        validated = _LLMResponseSchema(**raw)
        return validated.model_dump()
    except Exception:
        return None


def merge_collected_data(existing: dict, extracted: dict,
                         auto_filled: Optional[dict] = None) -> dict:
    """기존 수집 데이터에 새로 추출된 데이터를 병합한다.

    우선순위: extracted > auto_filled > existing
    (사용자 최신 입력이 가장 높은 우선순위)
    """
    merged = {**existing}

    if auto_filled:
        for key, value in auto_filled.items():
            if key in ALL_FIELDS and value is not None:
                merged[key] = value

    if extracted:
        for key, value in extracted.items():
            if key in ALL_FIELDS and value is not None:
                merged[key] = value

    return merged


def get_missing_fields(collected_data: dict) -> list:
    """아직 수집되지 않은 필수 필드 목록을 반환한다."""
    return [
        field for field in REQUIRED_FIELDS
        if field not in collected_data or collected_data[field] is None
    ]


def format_confirm_message(collected_data: dict) -> str:
    """확인 메시지를 생성한다."""
    vehicle = VEHICLE_DISPLAY.get(collected_data.get("vehicle_available"), "미입력")
    animal = ANIMAL_SIZE_DISPLAY.get(collected_data.get("max_animal_size"), "미입력")
    time_info = collected_data.get("available_time", "")
    waypoint_info = collected_data.get("waypoint", "")

    msg = (
        f"확인했습니다! 아래 내용으로 등록할게요.\n"
        f"날짜: {collected_data.get('available_date', '미입력')}\n"
        f"출발지: {collected_data.get('origin', '미입력')}\n"
        f"도착지: {collected_data.get('destination', '미입력')}\n"
        f"차량: {vehicle}\n"
        f"동물 크기: {animal}"
    )

    if time_info:
        msg += f"\n가용 시간: {time_info}"
    if waypoint_info:
        msg += f"\n환승 장소: {waypoint_info}"

    return msg
