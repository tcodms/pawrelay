from enum import Enum


class ChatbotState(str, Enum):
    COLLECTING = "COLLECTING"
    CONFIRMING = "CONFIRMING"
    COMPLETED = "COMPLETED"
