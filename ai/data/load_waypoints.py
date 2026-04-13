"""
waypoints 데이터 PostGIS 적재 스크립트

수집된 JSON 파일을 읽어 waypoints 테이블에 적재한다.
테이블이 없으면 자동 생성한다.

실행:
    python -m ai.data.load_waypoints --file data/waypoints.json
    python -m ai.data.load_waypoints --file data/shelter.json --file data/rest_area.json
"""

import argparse
import json
import os
from typing import Optional

import psycopg2
import psycopg2.extras

from ai.models.waypoint import WAYPOINT_TABLE_SQL, WaypointModel


def _get_connection(database_url: str) -> psycopg2.extensions.connection:
    """DATABASE_URL로 psycopg2 연결 반환."""
    return psycopg2.connect(database_url)


def _ensure_table(conn: psycopg2.extensions.connection) -> None:
    """waypoints 테이블 및 인덱스 생성 (없을 경우에만)."""
    with conn.cursor() as cur:
        cur.execute(WAYPOINT_TABLE_SQL)
    conn.commit()


def _load_records(
    conn: psycopg2.extensions.connection,
    waypoints: list[WaypointModel],
) -> tuple[int, int]:
    """waypoints 리스트를 DB에 적재하고 (성공, 실패) 건수를 반환."""
    inserted = 0
    skipped = 0

    insert_sql = """
        INSERT INTO waypoints (name, type, address, phone, geom, source)
        VALUES (%(name)s, %(type)s, %(address)s, %(phone)s,
                ST_GeomFromEWKT(%(geom)s), %(source)s)
        ON CONFLICT DO NOTHING
    """

    with conn.cursor() as cur:
        for waypoint in waypoints:
            try:
                cur.execute(insert_sql, waypoint.to_postgis_insert())
                inserted += 1
            except Exception as e:
                skipped += 1
                print(f"[경고] 적재 실패 ({waypoint.name}): {e}")

    conn.commit()
    return inserted, skipped


def load_from_file(filepath: str, database_url: str) -> None:
    """JSON 파일을 읽어 waypoints 테이블에 적재."""
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    waypoints: list[WaypointModel] = []
    for key, records in data.items():
        for record in records:
            try:
                waypoints.append(WaypointModel(**record))
            except Exception as e:
                print(f"[경고] 모델 변환 실패 ({key}): {e}")

    if not waypoints:
        print(f"[경고] 적재할 데이터 없음: {filepath}")
        return

    conn = _get_connection(database_url)
    try:
        _ensure_table(conn)
        inserted, skipped = _load_records(conn, waypoints)
        print(f"{filepath}: 적재 {inserted}건, 실패 {skipped}건")
    finally:
        conn.close()


def _main() -> None:
    """CLI 진입점: JSON 파일을 읽어 PostGIS에 적재."""
    parser = argparse.ArgumentParser(description="waypoints PostGIS 적재")
    parser.add_argument(
        "--file",
        action="append",
        required=True,
        help="적재할 JSON 파일 경로 (여러 번 지정 가능)",
    )
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL 환경변수를 설정해주세요.")

    for filepath in args.file:
        load_from_file(filepath, database_url)


if __name__ == "__main__":
    _main()
