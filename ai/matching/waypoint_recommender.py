"""
차량 유무에 따른 waypoints 추천 분기 로직

설계 문서 기준:
    - 차량 있음 → 휴게소(rest_area), 기차역(train), 버스터미널(bus)
    - 차량 없음 → 기차역(train) 위주

API 응답 형식 (api-spec.md 기준):
    {
        "waypoints": {
            "train": [...],
            "bus": [...],
            "rest_area": [...]
        }
    }
"""

from dataclasses import dataclass
from typing import Optional

import psycopg2
import psycopg2.extras

from ai.models.waypoint import WaypointType

# 반경 기본값 (km)
_DEFAULT_RADIUS_KM = 10

# 차량 유무별 추천 타입
_TYPES_WITH_VEHICLE = [WaypointType.REST_AREA, WaypointType.TRAIN, WaypointType.BUS]
_TYPES_WITHOUT_VEHICLE = [WaypointType.TRAIN]

# 타입별 최대 반환 건수 (합계 20건 이내, api-spec.md)
_MAX_TOTAL = 20
_MAX_PER_TYPE = 7

_NEARBY_SQL = """
    SELECT
        name,
        type,
        ST_Y(geom) AS latitude,
        ST_X(geom) AS longitude,
        address,
        phone,
        ST_Distance(
            geom::geography,
            ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
        ) / 1000.0 AS distance_km
    FROM waypoints
    WHERE type = %s
      AND ST_DWithin(
          geom::geography,
          ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
          %s
      )
    ORDER BY distance_km
    LIMIT %s
"""


@dataclass
class WaypointResult:
    """추천 waypoint 단건."""

    name: str
    type: str
    latitude: float
    longitude: float
    address: Optional[str]
    phone: Optional[str]
    distance_km: float


def recommend_waypoints(
    conn: psycopg2.extensions.connection,
    latitude: float,
    longitude: float,
    vehicle_available: bool,
    radius_km: float = _DEFAULT_RADIUS_KM,
) -> dict[str, list[WaypointResult]]:
    """차량 유무에 따라 근처 waypoints를 타입별로 추천.

    Args:
        conn: psycopg2 DB 연결
        latitude: 기준 위도
        longitude: 기준 경도
        vehicle_available: 차량 보유 여부
        radius_km: 검색 반경 (기본 10km)

    Returns:
        타입별 WaypointResult 리스트 딕셔너리
        예: {"train": [...], "bus": [...], "rest_area": [...]}
    """
    types = _TYPES_WITH_VEHICLE if vehicle_available else _TYPES_WITHOUT_VEHICLE
    result: dict[str, list[WaypointResult]] = {}
    remaining = _MAX_TOTAL

    for waypoint_type in types:
        if remaining <= 0:
            break
        limit = min(_MAX_PER_TYPE, remaining)
        rows = _query_nearby(conn, latitude, longitude, waypoint_type, radius_km, limit)
        result[waypoint_type.value] = rows
        remaining -= len(rows)

    return result


def _row_to_result(row: dict) -> WaypointResult:
    """DB 행을 WaypointResult로 변환한다."""
    return WaypointResult(
        name=row["name"],
        type=row["type"],
        latitude=row["latitude"],
        longitude=row["longitude"],
        address=row["address"],
        phone=row["phone"],
        distance_km=round(row["distance_km"], 2),
    )


def _query_nearby(
    conn: psycopg2.extensions.connection,
    latitude: float,
    longitude: float,
    waypoint_type: WaypointType,
    radius_km: float,
    limit: int = _MAX_PER_TYPE,
) -> list[WaypointResult]:
    """PostGIS로 반경 내 특정 타입 waypoints 조회."""
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(_NEARBY_SQL, (
            longitude, latitude,
            waypoint_type.value,
            longitude, latitude,
            radius_km * 1000,
            limit,
        ))
        rows = cur.fetchall()
    return [_row_to_result(row) for row in rows]
