from unittest.mock import AsyncMock, patch

import pytest

from ai.matching.chain_selector import _parse_response, select_chain


@pytest.fixture(autouse=True)
def _set_mock_provider_env(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")


_SAMPLE_CHAINS = [
    [
        {
            "schedule_id": 101,
            "volunteer_id": 201,
            "origin_area": "Gwangju",
            "destination_area": "Daejeon",
            "available_date": "2026-04-27",
            "available_time": "08:00",
            "estimated_arrival_time": "11:00",
            "vehicle_available": True,
            "max_animal_size": "small",
            "is_direct_apply": True,
        }
    ],
    [
        {
            "schedule_id": 102,
            "volunteer_id": 202,
            "origin_area": "Gwangju",
            "destination_area": "Seoul",
            "available_date": "2026-04-27",
            "available_time": "09:00",
            "estimated_arrival_time": "14:00",
            "vehicle_available": False,
            "max_animal_size": "small",
            "is_direct_apply": False,
        }
    ],
]

_SAMPLE_POST = {
    "id": 1,
    "animal_info": "Choco",
    "origin": "Gwangju",
    "destination": "Seoul",
    "scheduled_date": "2026-04-27",
}


def _valid_response(primary_index: int = 0) -> str:
    primary = _SAMPLE_CHAINS[primary_index]
    backups = [chain for i, chain in enumerate(_SAMPLE_CHAINS) if i != primary_index]
    response = {
        "chain": primary,
        "backup_candidates": backups,
        "matching_reason": "Direct applicant is included and the route is stable.",
    }
    return (
        str(response)
        .replace("'", '"')
        .replace("True", "true")
        .replace("False", "false")
    )


def test_parse_response_valid():
    result = _parse_response(_valid_response(0), _SAMPLE_CHAINS)
    assert result is not None
    assert result["chain"][0]["schedule_id"] == 101
    assert len(result["backup_candidates"]) == 1
    assert result["matching_reason"]


def test_parse_response_with_code_block():
    text = f"```json\n{_valid_response(1)}\n```"
    result = _parse_response(text, _SAMPLE_CHAINS)
    assert result is not None
    assert result["chain"][0]["schedule_id"] == 102


def test_parse_response_missing_key():
    text = '{"chain": [], "matching_reason": "missing backups"}'
    assert _parse_response(text, _SAMPLE_CHAINS) is None


def test_parse_response_invalid_backup_set():
    text = (
        "{"
        f"\"chain\": {_SAMPLE_CHAINS[0]!r}, "
        "\"backup_candidates\": [], "
        "\"matching_reason\": \"backup candidates are missing.\""
        "}"
    ).replace("'", '"').replace("True", "true").replace("False", "false")
    assert _parse_response(text, _SAMPLE_CHAINS) is None


@pytest.mark.asyncio
async def test_select_chain_success():
    with patch("ai.matching.chain_selector.get_llm_provider") as mock_get:
        mock_provider = AsyncMock()
        mock_provider.complete.return_value = _valid_response(0)
        mock_get.return_value = mock_provider

        result = await select_chain(_SAMPLE_CHAINS, _SAMPLE_POST)

        assert result["chain"][0]["schedule_id"] == 101
        assert len(result["backup_candidates"]) == 1
        assert mock_provider.complete.call_count == 1


@pytest.mark.asyncio
async def test_select_chain_retry_then_success():
    invalid = "not-json"
    valid = _valid_response(1)
    with patch("ai.matching.chain_selector.get_llm_provider") as mock_get:
        mock_provider = AsyncMock()
        mock_provider.complete.side_effect = [invalid, invalid, valid]
        mock_get.return_value = mock_provider

        result = await select_chain(_SAMPLE_CHAINS, _SAMPLE_POST)

        assert result["chain"][0]["schedule_id"] == 102
        assert mock_provider.complete.call_count == 3


@pytest.mark.asyncio
async def test_select_chain_all_fail_notifies_admin():
    with patch("ai.matching.chain_selector.get_llm_provider") as mock_get, patch(
        "ai.matching.chain_selector.notify_admin"
    ) as mock_notify:
        mock_provider = AsyncMock()
        mock_provider.complete.return_value = "not-json"
        mock_get.return_value = mock_provider

        with pytest.raises(ValueError, match="LLM chain selection failed"):
            await select_chain(_SAMPLE_CHAINS, _SAMPLE_POST)

        assert mock_provider.complete.call_count == 3
        mock_notify.assert_called_once()
