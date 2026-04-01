import asyncio
from ai.session.mock_session import MockSessionManager
from ai.errors import (
    InvalidInputError,
    SessionExpiredError,
    GeocodingFailedError,
    ScheduleSaveFailedError,
)


async def test_session_create_and_get():
    print("=== 세션 생성/조회 테스트 ===")

    manager = MockSessionManager()
    session_id = await manager.create(post_id=5, auto_filled={"available_date": "2026-04-10"})

    assert session_id is not None
    print(f"세션 생성: {session_id[:8]}...")

    session = await manager.get(session_id)
    assert session is not None
    assert session["state"] == "ASK_ORIGIN"
    assert session["post_id"] == 5
    print(f"세션 조회: state={session['state']}, post_id={session['post_id']}")

    print("=== 세션 생성/조회 테스트 성공 ===\n")


async def test_session_update():
    print("=== 세션 업데이트 테스트 ===")

    manager = MockSessionManager()
    session_id = await manager.create()

    result = await manager.update(session_id, {
        "state": "ASK_DESTINATION",
        "collected_data": {"origin": "광주광역시"},
    })

    assert result is True

    session = await manager.get(session_id)
    assert session["state"] == "ASK_DESTINATION"
    print(f"업데이트 후: state={session['state']}")

    print("=== 세션 업데이트 테스트 성공 ===\n")


async def test_session_delete():
    print("=== 세션 삭제 테스트 ===")

    manager = MockSessionManager()
    session_id = await manager.create()

    result = await manager.delete(session_id)
    assert result is True

    session = await manager.get(session_id)
    assert session is None
    print("삭제 후 조회: None")

    print("=== 세션 삭제 테스트 성공 ===\n")


async def test_session_expired():
    print("=== 세션 만료 테스트 ===")

    manager = MockSessionManager()
    session_id = await manager.create()

    manager._sessions[session_id]["created_at"] -= 3601

    session = await manager.get(session_id)
    assert session is None
    print("1시간 경과 후 조회: None (만료됨)")

    print("=== 세션 만료 테스트 성공 ===\n")


def test_error_codes():
    print("=== 에러 코드 테스트 ===")

    errors = [
        InvalidInputError(),
        SessionExpiredError(),
        GeocodingFailedError(),
        ScheduleSaveFailedError(),
    ]

    for error in errors:
        print(f"  {error.code}: {error.message}")
        assert error.code is not None

    print("=== 에러 코드 테스트 성공 ===\n")


if __name__ == "__main__":
    asyncio.run(test_session_create_and_get())
    asyncio.run(test_session_update())
    asyncio.run(test_session_delete())
    asyncio.run(test_session_expired())
    test_error_codes()
    print("모든 테스트 통과!")