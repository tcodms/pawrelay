import asyncio
import os

os.environ["LLM_PROVIDER"] = "mock"

from ai.chatbot.engine import ChatbotEngine
from ai.session.mock_session import MockSessionManager
from ai.errors import ParseFailedError, LLMError


def test_initial_message():
    print("=== 초기 메시지 테스트 ===")
    engine = ChatbotEngine()
    response = engine.get_initial_message()
    assert response["state"] == "COLLECTING"
    assert response["completed"] is False
    print(f"메시지: {response['message'][:50]}...")
    print("=== 성공 ===\n")


def test_post_entry():
    print("=== 게시판 진입 테스트 ===")
    auto_filled = {
        "available_date": "2026-04-10",
        "max_animal_size": "small",
    }
    engine = ChatbotEngine(post_id=5, auto_filled=auto_filled)
    response = engine.get_initial_message()
    assert "공고 정보" in response["message"]
    print(f"메시지: {response['message'][:80]}...")
    print("=== 성공 ===\n")


async def test_mock_process():
    print("=== Mock LLM 파싱 테스트 ===")
    engine = ChatbotEngine()
    response = await engine.process_input("광주에서 서울 가는데 차 있고 소형만 가능해요 4월 10일에")
    print(f"상태: {response['state']}")
    print(f"메시지: {response['message'][:80]}...")
    if response.get("collected_data"):
        print(f"수집 데이터: {response['collected_data']}")
    print("=== 성공 ===\n")


def test_confirm_register():
    print("=== 등록 확인 테스트 ===")
    engine = ChatbotEngine()
    engine.state = "CONFIRMING"
    engine.collected_data = {
        "origin": "광주광역시",
        "destination": "서울특별시",
        "available_date": "2026-04-10",
        "vehicle_available": True,
        "max_animal_size": "small",
    }
    response = engine._handle_confirm("등록하기")
    assert response["completed"] is True
    assert response["state"] == "COMPLETED"
    print(f"저장 데이터: {response['schedule_data']}")
    print("=== 성공 ===\n")


def test_confirm_retry():
    print("=== 수정하기 테스트 ===")
    engine = ChatbotEngine()
    engine.state = "CONFIRMING"
    response = engine._handle_confirm("수정하기")
    assert response["state"] == "COLLECTING"
    print("=== 성공 ===\n")


async def test_empty_input():
    print("=== 빈 입력 테스트 ===")
    engine = ChatbotEngine()
    response = await engine.process_input("")
    assert response.get("error") == "INVALID_INPUT"
    print(f"에러: {response['error']}")
    print("=== 성공 ===\n")


async def test_session_manager():
    print("=== 세션 매니저 테스트 ===")
    manager = MockSessionManager()
    session_id = await manager.create(post_id=5, auto_filled={"available_date": "2026-04-10"})
    assert session_id is not None
    print(f"세션 생성: {session_id[:8]}...")

    session = await manager.get(session_id)
    assert session["post_id"] == 5
    print(f"세션 조회: state={session['state']}")

    await manager.update(session_id, {"state": "CONFIRMING"})
    session = await manager.get(session_id)
    assert session["state"] == "CONFIRMING"
    print(f"세션 업데이트: state={session['state']}")

    await manager.delete(session_id)
    session = await manager.get(session_id)
    assert session is None
    print("세션 삭제 확인")
    print("=== 성공 ===\n")


def test_error_codes():
    print("=== 에러 코드 테스트 ===")
    errors = [ParseFailedError(), LLMError()]
    for error in errors:
        print(f"  {error.code}: {error.message}")
    print("=== 성공 ===\n")


if __name__ == "__main__":
    test_initial_message()
    test_post_entry()
    asyncio.run(test_mock_process())
    test_confirm_register()
    test_confirm_retry()
    asyncio.run(test_empty_input())
    asyncio.run(test_session_manager())
    test_error_codes()
    print("모든 테스트 통과!")