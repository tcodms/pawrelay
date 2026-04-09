import os

import pytest

os.environ["LLM_PROVIDER"] = "mock"

from ai.chatbot.engine import ChatbotEngine


@pytest.mark.asyncio
async def test_initial_message():
    engine = ChatbotEngine()
    msg = engine.get_initial_message()
    assert msg["state"] == "COLLECTING"
    assert msg["completed"] is False


@pytest.mark.asyncio
async def test_empty_input_returns_error():
    engine = ChatbotEngine()
    result = await engine.process_input("")
    assert result["error"] == "INVALID_INPUT"


@pytest.mark.asyncio
async def test_input_too_long_returns_error():
    engine = ChatbotEngine()
    result = await engine.process_input("a" * 501)
    assert result["error"] == "INVALID_INPUT"


@pytest.mark.asyncio
async def test_full_collection_reaches_confirming():
    """Mock이 all_complete=True를 반환하므로 한 번의 입력으로 CONFIRMING에 도달해야 한다."""
    engine = ChatbotEngine()
    result = await engine.process_input("광주에서 서울 이번주 토요일 차 있고 소형")
    assert result["state"] == "CONFIRMING"
    assert result["completed"] is False
    assert "등록하기" in result["options"]


@pytest.mark.asyncio
async def test_confirm_completes():
    engine = ChatbotEngine()
    await engine.process_input("광주에서 서울")
    result = await engine.process_input("등록하기")
    assert result["state"] == "COMPLETED"
    assert result["completed"] is True


@pytest.mark.asyncio
async def test_modify_resets_state():
    engine = ChatbotEngine()
    await engine.process_input("광주에서 서울")
    result = await engine.process_input("수정하기")
    assert result["state"] == "COLLECTING"


@pytest.mark.asyncio
async def test_auto_filled_applied():
    engine = ChatbotEngine(
        post_id=1,
        auto_filled={"available_date": "2026-04-10", "max_animal_size": "small"},
    )
    assert engine.collected_data.get("available_date") == "2026-04-10"
    assert engine.collected_data.get("max_animal_size") == "small"


@pytest.mark.asyncio
async def test_state_rollback_on_llm_error(monkeypatch):
    """LLM 호출 실패 시 세션 상태가 이전 상태로 롤백되어야 한다."""
    engine = ChatbotEngine()
    engine.state = "COLLECTING"
    engine.collected_data = {"origin": "광주광역시"}

    async def mock_fail(*args, **kwargs):
        raise RuntimeError("LLM 오류")

    monkeypatch.setattr(engine.provider, "complete", mock_fail)

    result = await engine.process_input("서울로 가고 싶어요")
    assert result["error"] == "LLM_ERROR"
    assert engine.state == "COLLECTING"
    assert engine.collected_data == {"origin": "광주광역시"}
