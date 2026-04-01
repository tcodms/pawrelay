from enum import Enum


class ChatState(Enum):
    ASK_ORIGIN = "ASK_ORIGIN"
    ASK_DESTINATION = "ASK_DESTINATION"
    ASK_DATE = "ASK_DATE"
    ASK_VEHICLE = "ASK_VEHICLE"
    ASK_ANIMAL_SIZE = "ASK_ANIMAL_SIZE"
    CONFIRM = "CONFIRM"
    COMPLETED = "COMPLETED"


STATE_CONFIG = {
    ChatState.ASK_ORIGIN: {
        "message": "어느 지역에서 출발하실 수 있나요?",
        "input_type": "address_search",
        "options": None,
    },
    ChatState.ASK_DESTINATION: {
        "message": "어디까지 이동하실 수 있나요?",
        "input_type": "address_search",
        "options": None,
    },
    ChatState.ASK_DATE: {
        "message": "이동 가능한 날짜를 선택해주세요.",
        "input_type": "date_picker",
        "options": None,
    },
    ChatState.ASK_VEHICLE: {
        "message": "차량이 있으신가요?",
        "input_type": "buttons",
        "options": ["있어요", "없어요"],
    },
    ChatState.ASK_ANIMAL_SIZE: {
        "message": "탑승 가능한 동물 크기를 선택해주세요.",
        "input_type": "buttons",
        "options": ["소형 (5kg 이하)", "중형 (5~15kg)", "대형 (15kg 이상)"],
    },
    ChatState.CONFIRM: {
        "message": "입력하신 정보를 확인해주세요.",
        "input_type": "buttons",
        "options": ["등록하기", "처음부터 다시"],
    },
    ChatState.COMPLETED: {
        "message": "동선 등록이 완료되었습니다!",
        "input_type": None,
        "options": None,
    },
}

STATE_ORDER = [
    ChatState.ASK_ORIGIN,
    ChatState.ASK_DESTINATION,
    ChatState.ASK_DATE,
    ChatState.ASK_VEHICLE,
    ChatState.ASK_ANIMAL_SIZE,
    ChatState.CONFIRM,
    ChatState.COMPLETED,
]

SKIP_STATES_WITH_POST = {
    ChatState.ASK_DATE,
    ChatState.ASK_ANIMAL_SIZE,
}