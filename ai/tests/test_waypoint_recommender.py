"""
waypoint_recommender 단위 테스트

DB 연결 없이 mock으로 분기 로직만 검증한다.
"""

from unittest.mock import MagicMock, patch

import pytest

from ai.matching.waypoint_recommender import (
    WaypointResult,
    _TYPES_WITH_VEHICLE,
    _TYPES_WITHOUT_VEHICLE,
    recommend_waypoints,
)
from ai.models.waypoint import WaypointType


def _make_mock_conn(rows: list[dict]) -> MagicMock:
    """DictCursor를 흉내내는 mock DB 연결 반환."""
    mock_cursor = MagicMock()
    mock_cursor.__enter__ = lambda s: s
    mock_cursor.__exit__ = MagicMock(return_value=False)
    mock_cursor.fetchall.return_value = [
        {
            "name": r["name"],
            "type": r["type"],
            "latitude": r.get("latitude", 37.0),
            "longitude": r.get("longitude", 127.0),
            "address": r.get("address"),
            "phone": r.get("phone"),
            "distance_km": r.get("distance_km", 5.0),
        }
        for r in rows
    ]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn


def test_vehicle_true_includes_rest_area():
    """차량 있음 시 rest_area 타입이 포함되어야 한다."""
    assert WaypointType.REST_AREA in _TYPES_WITH_VEHICLE


def test_vehicle_false_excludes_rest_area():
    """차량 없음 시 rest_area 타입이 포함되지 않아야 한다."""
    assert WaypointType.REST_AREA not in _TYPES_WITHOUT_VEHICLE


def test_vehicle_false_only_train():
    """차량 없음 시 train만 추천해야 한다."""
    assert _TYPES_WITHOUT_VEHICLE == [WaypointType.TRAIN]


def test_recommend_with_vehicle_returns_all_types():
    """차량 있음 시 결과 키에 train, bus, rest_area가 모두 있어야 한다."""
    mock_conn = _make_mock_conn([
        {"name": "천안역", "type": "train"},
    ])

    result = recommend_waypoints(mock_conn, 36.8, 127.1, vehicle_available=True)

    assert "train" in result
    assert "bus" in result
    assert "rest_area" in result


def test_recommend_without_vehicle_returns_only_train():
    """차량 없음 시 결과 키에 train만 있어야 한다."""
    mock_conn = _make_mock_conn([
        {"name": "천안역", "type": "train"},
    ])

    result = recommend_waypoints(mock_conn, 36.8, 127.1, vehicle_available=False)

    assert "train" in result
    assert "bus" not in result
    assert "rest_area" not in result


def test_recommend_result_type():
    """반환값이 WaypointResult 인스턴스여야 한다."""
    mock_conn = _make_mock_conn([
        {"name": "천안역", "type": "train", "distance_km": 3.5},
    ])

    result = recommend_waypoints(mock_conn, 36.8, 127.1, vehicle_available=False)

    assert len(result["train"]) == 1
    assert isinstance(result["train"][0], WaypointResult)
    assert result["train"][0].name == "천안역"
