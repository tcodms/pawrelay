import json


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


def parse_llm_response(response_text):
    """LLM 응답 JSON을 파싱한다."""
    try:
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(cleaned)
    except (json.JSONDecodeError, IndexError):
        return None


def merge_collected_data(existing, extracted, auto_filled=None):
    """기존 수집 데이터에 새로 추출된 데이터를 병합한다."""
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


def get_missing_fields(collected_data):
    """아직 수집되지 않은 필수 필드 목록을 반환한다."""
    missing = []
    for field in REQUIRED_FIELDS:
        if field not in collected_data or collected_data[field] is None:
            missing.append(field)
    return missing


def format_confirm_message(collected_data):
    """확인 메시지를 생성한다."""
    vehicle = VEHICLE_DISPLAY.get(collected_data.get("vehicle_available"), "미입력")
    animal = ANIMAL_SIZE_DISPLAY.get(collected_data.get("max_animal_size"), "미입력")
    time_info = collected_data.get("available_time", "")
    waypoint_info = collected_data.get("waypoint", "")

    msg = (
        f"확인했습니다! 아래 내용으로 등록할게요.\n"
        f"📅 날짜: {collected_data.get('available_date', '미입력')}\n"
        f"📍 출발지: {collected_data.get('origin', '미입력')}\n"
        f"📍 도착지: {collected_data.get('destination', '미입력')}\n"
        f"🚗 차량: {vehicle}\n"
        f"🐾 동물 크기: {animal}"
    )

    if time_info:
        msg += f"\n🕐 가용 시간: {time_info}"
    if waypoint_info:
        msg += f"\n🔄 환승 장소: {waypoint_info}"

    return msg