import json
import uuid
from datetime import date

from fastapi import HTTPException
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.chatbot.mock_engine import MockChatbotEngine
from app.repositories import volunteer_repo
from app.schemas.chatbot import ChatMessageResponse, ChatSessionResponse
from app.services.geocoding_service import geocode

_SESSION_TTL = 3600  # 1시간
_engine = MockChatbotEngine()


def _session_key(session_id: str) -> str:
    return f"chatbot:session:{session_id}"


async def _load_session(redis: Redis, session_id: str) -> dict:
    raw = await redis.get(_session_key(session_id))
    if not raw:
        raise HTTPException(status_code=404, detail={"error": "SESSION_NOT_FOUND"})
    return json.loads(raw)


async def _save_session(redis: Redis, session_id: str, session: dict) -> None:
    await redis.setex(_session_key(session_id), _SESSION_TTL, json.dumps(session))


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
        session = {
            "volunteer_id": volunteer_id,
            "post_id": post_id,
            "state": "ASK_ORIGIN",
            "collected_data": {},
            "auto_filled": {},
        }

    result = _engine.process_input(
        message=message,
        state=session["state"],
        collected_data=session["collected_data"],
    )

    session["state"] = result.next_state
    session["collected_data"] = result.collected_data

    schedule_id = None
    if result.completed:
        schedule_id = await _save_schedule(db, volunteer_id, session)
        await redis.delete(_session_key(session_id))
    else:
        await _save_session(redis, session_id, session)

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


async def get_session(redis: Redis, session_id: str) -> ChatSessionResponse:
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
        raise HTTPException(status_code=404, detail={"error": "SESSION_NOT_FOUND"})


async def _save_schedule(db: AsyncSession, volunteer_id: int, session: dict) -> int:
    data = session["collected_data"]

    try:
        origin_lat, origin_lng = await geocode(data["origin"])
        dest_lat, dest_lng = await geocode(data["destination"])
    except (ValueError, KeyError) as err:
        raise HTTPException(status_code=400, detail={"error": "GEOCODING_FAILED"}) from err

    route_wkt = (
        f"SRID=4326;LINESTRING({origin_lng} {origin_lat}, {dest_lng} {dest_lat})"
    )

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
