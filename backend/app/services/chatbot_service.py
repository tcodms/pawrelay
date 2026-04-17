"""챗봇 서비스 - LLMChatbotEngine + Redis 세션 연동."""
import json
import re
import uuid
from datetime import date

from fastapi import HTTPException
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.chatbot.llm_engine import EngineResult, LLMChatbotEngine
from app.repositories import volunteer_repo
from app.schemas.chatbot import ChatMessageResponse, ChatSessionResponse
from app.services import geocoding_service

_SESSION_TTL = 3600  # 1시간
_engine = LLMChatbotEngine()

_STATE_WELCOME = {
    "ASK_ORIGIN": ("address_search", None, "어느 지역에서 출발하실 수 있나요?"),
    "ASK_DESTINATION": ("address_search", None, "목적지는 어디인가요?"),
    "ASK_DATE": ("date_picker", None, "봉사 가능한 날짜를 선택해주세요."),
    "ASK_VEHICLE": ("buttons", ["있어요", "없어요"], "차량이 있으신가요?"),
    "ASK_ANIMAL_SIZE": (
        "buttons",
        ["소형 (5kg 이하)", "중형 (5~15kg)", "대형 (15kg 이상)"],
        "이동 가능한 동물 크기를 선택해주세요.",
    ),
}


def _build_welcome_response(session_id: str, session: dict) -> ChatMessageResponse:
    """message=null 첫 진입 시 현재 state에 맞는 안내 메시지를 반환한다."""
    state = session.get("state", "ASK_ORIGIN")
    input_type, options, msg = _STATE_WELCOME.get(state, (None, None, "동선을 입력해주세요."))
    if state == "ASK_ORIGIN":
        msg = "안녕하세요! 이동봉사 동선을 등록할게요.\n" + msg
    return ChatMessageResponse(
        session_id=session_id, state=state, message=msg,
        input_type=input_type, options=options,
        auto_filled=session.get("auto_filled") or None,
        completed=False, schedule_id=None,
    )


def _session_key(session_id: str) -> str:
    return f"chatbot:session:{session_id}"


async def _load_session(redis: Redis, session_id: str) -> dict:
    """Redis에서 세션을 조회한다. 없으면 SESSION_EXPIRED 에러."""
    raw = await redis.get(_session_key(session_id))
    if not raw:
        raise HTTPException(status_code=404, detail={"error": "SESSION_EXPIRED"})
    return json.loads(raw)


def _check_owner(session: dict, volunteer_id: int) -> None:
    """세션 소유자 검증. 불일치 시 403 반환."""
    if session.get("volunteer_id") != volunteer_id:
        raise HTTPException(status_code=403, detail={"error": "FORBIDDEN"})


async def _save_session(redis: Redis, session_id: str, session: dict) -> None:
    await redis.setex(_session_key(session_id), _SESSION_TTL, json.dumps(session))


def _new_session(volunteer_id: int, post_id: int | None) -> dict:
    """신규 세션 dict를 생성한다."""
    return {
        "volunteer_id": volunteer_id,
        "post_id": post_id,
        "state": "ASK_ORIGIN",
        "collected_data": {},
        "auto_filled": {},
    }


async def _build_route_wkt(origin: str, destination: str) -> str | None:
    """출발지/목적지 텍스트를 Geocoding해 EWKT LineString을 생성한다. 실패 시 None 반환."""
    try:
        o_lat, o_lng = await geocoding_service.geocode(origin)
        d_lat, d_lng = await geocoding_service.geocode(destination)
        return f"SRID=4326;LINESTRING({o_lng} {o_lat}, {d_lng} {d_lat})"
    except ValueError:
        return None


def _validate_available_time(value: str | None) -> str | None:
    """HH:MM 형식(5자)만 허용. 그 외는 None 반환."""
    if value and re.fullmatch(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]", value):
        return value
    return None


_SCHEDULE_REQUIRED_KEYS = ("origin", "destination", "available_date", "vehicle_available", "max_animal_size")


def _validate_schedule_data(data: dict) -> date:
    """collected_data 필수 키 및 날짜 형식 검증. 유효하면 available_date 반환."""
    missing = [k for k in _SCHEDULE_REQUIRED_KEYS if k not in data]
    if missing:
        raise ValueError(f"collected_data 필수 키 누락: {missing}")
    try:
        return date.fromisoformat(data["available_date"])
    except ValueError as e:
        raise ValueError(f"available_date 형식 오류: {data['available_date']}") from e


def _build_schedule_kwargs(
    data: dict, volunteer_id: int, post_id: int | None, avail_date: date, route_wkt: str | None
) -> dict:
    """create_schedule 호출 인자 dict를 생성한다."""
    return {
        "volunteer_id": volunteer_id,
        "post_id": post_id,
        "route_description": f"{data['origin']} → {data['destination']}",
        "origin_area": data["origin"],
        "destination_area": data["destination"],
        "available_date": avail_date,
        "available_time": _validate_available_time(data.get("available_time")),
        "vehicle_available": data["vehicle_available"],
        "max_animal_size": data["max_animal_size"],
        "route_wkt": route_wkt,
    }


async def _save_schedule(
    db: AsyncSession, volunteer_id: int, session: dict
) -> int:
    """completed 시 volunteer_schedules에 저장하고 id를 반환한다."""
    data = session["collected_data"]
    avail_date = _validate_schedule_data(data)
    route_wkt = await _build_route_wkt(data["origin"], data["destination"])
    kwargs = _build_schedule_kwargs(data, volunteer_id, session.get("post_id"), avail_date, route_wkt)
    schedule = await volunteer_repo.create_schedule(db=db, **kwargs)
    return schedule.id


def _update_session_fields(session: dict, result: EngineResult) -> None:
    """엔진 결과를 세션 dict에 반영한다."""
    session["state"] = result.next_state
    session["collected_data"] = result.collected_data
    if result.next_state == "ASK_ORIGIN":
        session.pop("schedule_id", None)


async def _finalize_session(
    redis: Redis,
    db: AsyncSession,
    session_id: str,
    session: dict,
    result: EngineResult,
    volunteer_id: int,
) -> int | None:
    """세션 상태를 업데이트하고 저장(또는 삭제)한다. 완료 시 schedule_id 반환."""
    _update_session_fields(session, result)
    if result.completed:
        schedule_id = session.get("schedule_id") or await _save_schedule(db, volunteer_id, session)
        session["schedule_id"] = schedule_id
        await _save_session(redis, session_id, session)
        await redis.delete(_session_key(session_id))
        return schedule_id
    await _save_session(redis, session_id, session)
    return None


def _build_response(
    session_id: str, result: EngineResult, session: dict, schedule_id: int | None
) -> ChatMessageResponse:
    return ChatMessageResponse(
        session_id=session_id,
        state=result.next_state,
        message=result.message,
        input_type=result.input_type,
        options=result.options,
        auto_filled=session.get("auto_filled") or None,
        completed=result.completed,
        schedule_id=schedule_id,
    )


async def _resolve_session(
    redis: Redis, volunteer_id: int, session_id: str | None, post_id: int | None
) -> tuple[str, dict]:
    """기존 세션 조회 또는 신규 세션 생성 후 (session_id, session) 반환."""
    if session_id:
        session = await _load_session(redis, session_id)
        _check_owner(session, volunteer_id)
        return session_id, session
    return str(uuid.uuid4()), _new_session(volunteer_id, post_id)


async def send_message(
    redis: Redis,
    db: AsyncSession,
    volunteer_id: int,
    session_id: str | None,
    post_id: int | None,
    message: str | None,
) -> ChatMessageResponse:
    session_id, session = await _resolve_session(redis, volunteer_id, session_id, post_id)
    if message is None:
        await _save_session(redis, session_id, session)
        return _build_welcome_response(session_id, session)
    result = await _engine.process_input(
        message=message, state=session["state"],
        collected_data=session["collected_data"],
        post_id=session.get("post_id"), auto_filled=session.get("auto_filled", {}),
    )
    schedule_id = await _finalize_session(redis, db, session_id, session, result, volunteer_id)
    return _build_response(session_id, result, session, schedule_id)


async def get_session(redis: Redis, session_id: str, volunteer_id: int) -> ChatSessionResponse:
    """FE 새로고침 시 마지막 state 복원."""
    session = await _load_session(redis, session_id)
    _check_owner(session, volunteer_id)
    return ChatSessionResponse(
        session_id=session_id,
        state=session["state"],
        collected_data=session["collected_data"],
        auto_filled=session.get("auto_filled") or None,
    )


async def delete_session(redis: Redis, session_id: str, volunteer_id: int) -> None:
    session = await _load_session(redis, session_id)
    _check_owner(session, volunteer_id)
    await redis.delete(_session_key(session_id))
