import pytest

from ai.errors import (
    GeocodingFailedError,
    InvalidInputError,
    LLMError,
    ParseFailedError,
    ScheduleSaveFailedError,
    SessionExpiredError,
)
from ai.session.mock_session import MockSessionManager


@pytest.mark.asyncio
async def test_session_create_and_get():
    manager = MockSessionManager()
    session_id = await manager.create(post_id=5, auto_filled={"available_date": "2026-04-10"})
    assert session_id is not None

    session = await manager.get(session_id)
    assert session is not None
    assert session["state"] == "COLLECTING"
    assert session["post_id"] == 5
    assert session["auto_filled"]["available_date"] == "2026-04-10"


@pytest.mark.asyncio
async def test_session_update():
    manager = MockSessionManager()
    session_id = await manager.create()

    result = await manager.update(session_id, {
        "state": "CONFIRMING",
        "collected_data": {"origin": "광주광역시"},
    })
    assert result is True

    session = await manager.get(session_id)
    assert session["state"] == "CONFIRMING"
    assert session["collected_data"]["origin"] == "광주광역시"


@pytest.mark.asyncio
async def test_session_delete():
    manager = MockSessionManager()
    session_id = await manager.create()

    result = await manager.delete(session_id)
    assert result is True

    session = await manager.get(session_id)
    assert session is None


@pytest.mark.asyncio
async def test_session_expired_raises():
    """만료된 세션을 get() 하면 SessionExpiredError가 발생해야 한다."""
    manager = MockSessionManager()
    session_id = await manager.create()

    # 만료 시뮬레이션
    manager._sessions[session_id]["created_at"] -= 3601

    with pytest.raises(SessionExpiredError):
        await manager.get(session_id)


@pytest.mark.asyncio
async def test_session_isolation():
    """get()이 deepcopy를 반환해 원본 세션이 오염되지 않아야 한다."""
    manager = MockSessionManager()
    session_id = await manager.create(auto_filled={"origin": "광주광역시"})

    session = await manager.get(session_id)
    session["auto_filled"]["origin"] = "서울특별시"

    original = await manager.get(session_id)
    assert original["auto_filled"]["origin"] == "광주광역시"


def test_all_error_codes():
    """모든 에러 클래스가 code와 message를 가져야 한다."""
    errors = [
        InvalidInputError(),
        SessionExpiredError(),
        GeocodingFailedError(),
        ScheduleSaveFailedError(),
        ParseFailedError(),
        LLMError(),
    ]
    for error in errors:
        assert error.code is not None
        assert error.message is not None
