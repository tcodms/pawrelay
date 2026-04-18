import pytest

from unittest.mock import AsyncMock, patch


@pytest.fixture(autouse=True)
def _set_mock_provider_env(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")

from ai.matching.chain_selector import _parse_response, select_chain

# 테스트용 더미 데이터
_SAMPLE_CHAINS = [
    [
        {
            "volunteer_name": "김봉사",
            "origin_area": "광주광역시",
            "destination_area": "대전광역시",
            "available_date": "2026-04-20",
            "vehicle_available": True,
        }
    ],
    [
        {
            "volunteer_name": "이봉사",
            "origin_area": "광주광역시",
            "destination_area": "서울특별시",
            "available_date": "2026-04-20",
            "vehicle_available": False,
        }
    ],
]

_SAMPLE_POST = {
    "id": 1,
    "animal_info": "말티즈 3kg",
    "origin": "광주광역시",
    "destination": "서울특별시",
    "scheduled_date": "2026-04-20",
}


# ── 1. _parse_response 단위 테스트 ──────────────────────────────────────

def test_parse_response_valid():
    text = '{"selected_chain_index": 0, "matching_reason": "동선이 연속적입니다. 인계 시간도 충분합니다."}'
    result = _parse_response(text)
    assert result["selected_chain_index"] == 0
    assert "matching_reason" in result


def test_parse_response_with_code_block():
    text = '```json\n{"selected_chain_index": 1, "matching_reason": "최적의 경로입니다. 차량 보유로 이동이 원활합니다."}\n```'
    result = _parse_response(text)
    assert result is not None
    assert result["selected_chain_index"] == 1


def test_parse_response_missing_key():
    text = '{"selected_chain_index": 0}'  # matching_reason 없음
    assert _parse_response(text) is None


def test_parse_response_invalid_json():
    assert _parse_response("이건 JSON이 아닙니다") is None


# ── 2. select_chain 정상 동작 ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_select_chain_success():
    valid_response = '{"selected_chain_index": 0, "matching_reason": "동선 연속성이 우수합니다. 인계 시간 간격이 적절합니다."}'
    with patch("ai.matching.chain_selector.get_llm_provider") as mock_get:
        mock_provider = AsyncMock()
        mock_provider.complete.return_value = valid_response
        mock_get.return_value = mock_provider

        result = await select_chain(_SAMPLE_CHAINS, _SAMPLE_POST)

        assert result["selected_chain_index"] == 0
        assert "matching_reason" in result
        assert mock_provider.complete.call_count == 1


# ── 3. 파싱 실패 재시도 ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_select_chain_retry_then_success():
    invalid = "파싱 불가 응답"
    valid = '{"selected_chain_index": 1, "matching_reason": "3번째 시도에 성공했습니다. 최적 경로를 선택했습니다."}'
    with patch("ai.matching.chain_selector.get_llm_provider") as mock_get:
        mock_provider = AsyncMock()
        mock_provider.complete.side_effect = [invalid, invalid, valid]
        mock_get.return_value = mock_provider

        result = await select_chain(_SAMPLE_CHAINS, _SAMPLE_POST)

        assert result["selected_chain_index"] == 1
        assert mock_provider.complete.call_count == 3


# ── 4. 재시도 소진 + notify_admin ────────────────────────────────────────

@pytest.mark.asyncio
async def test_select_chain_all_fail_notifies_admin():
    with patch("ai.matching.chain_selector.get_llm_provider") as mock_get, \
         patch("ai.matching.chain_selector.notify_admin") as mock_notify:
        mock_provider = AsyncMock()
        mock_provider.complete.return_value = "파싱 불가 응답"
        mock_get.return_value = mock_provider

        with pytest.raises(ValueError, match="LLM 체인 선택 실패"):
            await select_chain(_SAMPLE_CHAINS, _SAMPLE_POST)

        assert mock_provider.complete.call_count == 3
        mock_notify.assert_called_once()
