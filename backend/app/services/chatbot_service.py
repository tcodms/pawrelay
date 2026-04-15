"""챗봇 서비스 - LLMChatbotEngine + Redis 세션 연동."""
import json
import uuid
from datetime import date

from fastapi import HTTPException
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.chatbot.llm_engine import EngineResult, LLMChatbotEngine
from app.repositories import volunteer_repo
from app.schemas.chatbot import ChatMessageResponse, ChatSessionResponse

_SESSION_TTL = 3600  # 1시간
_engine = LLMChatbotEngine()


def _session_key(session_id: str) -> str:
    return f"chatbot:session:{session_id}"


async def _load_session(redis: Redis, session_id: str) -> dict:
    """Redis에서 세션을 조회한다. 없으면 SESSION_EXPIRED 에러."""
    raw = await redis.get(_session_key(session_id))
    if not raw:
        raise HTTPException(status_code=404, detail={"error": "SESSION_EXPIRED"})
    return json.loads(raw)


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
        "coordinates": {},
    }


def _build_route_wkt(coords: dict) -> str | None:
    """저장된 좌표로 EWKT LineString을 생성한다. 좌표 없으면 None 반환."""
    origin = coords.get("origin", {})
    dest = coords.get("destination", {})
    if not (origin.get("lat") and dest.get("lat")):
        return None
    return (
        f"SRID=4326;LINESTRING"
        f"({origin['lng']} {origin['lat']}, {dest['lng']} {dest['lat']})"
    )


async def _save_schedule(
    db: AsyncSession, volunteer_id: int, session: dict
) -> int:
    """completed 시 volunteer_schedules에 저장하고 id를 반환한다."""
    data = session["collected_data"]
    route_wkt = _build_route_wkt(session.get("coordinates", {}))
    schedule = await volunteer_repo.create_schedule(
        db=db,
        volunteer_id=volunteer_id,
        post_id=session.get("post_id"),
        route_description=f"{data['origin']} → {data['destination']}",
        origin_area=data["origin"],
        destination_area=data["destination"],
        available_date=date.fromisoformat(data["available_date"]),
        available_time=data.get("available_time"),
        vehicle_available=data["vehicle_available"],
        max_animal_size=data["max_animal_size"],
        route_wkt=route_wkt,
    )
    return schedule.id


async def _finalize_session(
    redis: Redis,
    db: AsyncSession,
    session_id: str,
    session: dict,
    result: EngineResult,
    volunteer_id: int,
) -> int | None:
    """세션 상태를 업데이트하고 저장(또는 삭제)한다. 완료 시 schedule_id 반환."""
    session["state"] = result.next_state
    session["collected_data"] = result.collected_data
    session.setdefault("coordinates", {}).update(result.coordinates)
    if result.completed:
        schedule_id = await _save_schedule(db, volunteer_id, session)
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


async def send_message(
    redis: Redis,
    db: AsyncSession,
    volunteer_id: int,
    session_id: str | None,
    post_id: int | None,
    message: str | None,
) -> ChatMessageResponse:
    if session_id:
        session = await _load_session(redis, session_id)
    else:
        session_id = str(uuid.uuid4())
        session = _new_session(volunteer_id, post_id)

    result = await _engine.process_input(
        message=message,
        state=session["state"],
        collected_data=session["collected_data"],
        post_id=session.get("post_id"),
        auto_filled=session.get("auto_filled", {}),
    )
    schedule_id = await _finalize_session(
        redis, db, session_id, session, result, volunteer_id
    )
    return _build_response(session_id, result, session, schedule_id)


async def get_session(redis: Redis, session_id: str) -> ChatSessionResponse:
    """FE 새로고침 시 마지막 state 복원."""
    session = await _load_session(redis, session_id)
    return ChatSessionResponse(
        session_id=session_id,
        state=session["state"],
        collected_data=session["collected_data"],
        auto_filled=session.get("auto_filled") or None,
    )


async def delete_session(redis: Redis, session_id: str) -> None:
    deleted = await redis.delete(_session_key(session_id))
    if not deleted:
        raise HTTPException(status_code=404, detail={"error": "SESSION_EXPIRED"})
