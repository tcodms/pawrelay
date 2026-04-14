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
import logging
import os

import psycopg2
from pydantic import ValidationError

from ai.models.waypoint import WAYPOINT_TABLE_SQL, WAYPOINT_UNIQUE_INDEX_SQL, WaypointModel

logger = logging.getLogger(__name__)

_INSERT_SQL = """
    INSERT INTO waypoints (name, type, address, phone, geom, source)
    VALUES (%(name)s, %(type)s, %(address)s, %(phone)s,
            ST_GeomFromEWKT(%(geom)s), %(source)s)
    ON CONFLICT (name, type) DO NOTHING
"""


def _get_connection(database_url: str) -> psycopg2.extensions.connection:
    """DATABASE_URL로 psycopg2 연결 반환."""
    return psycopg2.connect(database_url)


def _ensure_table(conn: psycopg2.extensions.connection) -> None:
    """waypoints 테이블 및 인덱스 생성 (없을 경우에만)."""
    with conn.cursor() as cur:
        cur.execute(WAYPOINT_TABLE_SQL)
    conn.commit()
    _ensure_unique_index(conn)


def _ensure_unique_index(conn: psycopg2.extensions.connection) -> None:
    """UNIQUE 인덱스 생성. 중복 데이터가 있으면 경고 후 skip."""
    try:
        with conn.cursor() as cur:
            cur.execute(WAYPOINT_UNIQUE_INDEX_SQL)
        conn.commit()
    except psycopg2.Error as e:
        conn.rollback()
        logger.error("UNIQUE 인덱스 생성 실패: %s", e)
        raise RuntimeError(
            "waypoints(name, type) UNIQUE 인덱스를 생성하지 못해 적재를 중단합니다."
        ) from e


def _load_records(
    conn: psycopg2.extensions.connection,
    waypoints: list[WaypointModel],
) -> tuple[int, int, int]:
    """waypoints 리스트를 DB에 적재하고 (성공, 중복, 실패) 건수를 반환."""
    inserted = 0
    duplicated = 0
    skipped = 0

    with conn.cursor() as cur:
        for waypoint in waypoints:
            try:
                cur.execute("SAVEPOINT sp")
                cur.execute(_INSERT_SQL, waypoint.to_postgis_insert())
                if cur.rowcount:
                    inserted += 1
                else:
                    duplicated += 1
                cur.execute("RELEASE SAVEPOINT sp")
            except psycopg2.Error as e:
                skipped += 1
                logger.warning("적재 실패 (%s): %s", waypoint.name, e)
                cur.execute("ROLLBACK TO SAVEPOINT sp")
                try:
                    cur.execute("RELEASE SAVEPOINT sp")
                except psycopg2.Error as release_err:
                    logger.warning("SAVEPOINT 해제 실패: %s", release_err)

    conn.commit()
    return inserted, duplicated, skipped


def _parse_json_to_waypoints(data: dict) -> list[WaypointModel]:
    """JSON 데이터를 WaypointModel 리스트로 변환."""
    waypoints = []
    for key, records in data.items():
        if not isinstance(records, list):
            logger.warning("리스트가 아닌 값 건너뜀 (%s): %s", key, type(records).__name__)
            continue
        for record in records:
            try:
                waypoints.append(WaypointModel(**record))
            except (ValidationError, TypeError) as e:
                logger.warning("모델 변환 실패 (%s): %s", key, e)
    return waypoints


def load_from_file(filepath: str, database_url: str) -> None:
    """JSON 파일을 읽어 waypoints 테이블에 적재."""
    with open(filepath, encoding="utf-8") as f:
        waypoints = _parse_json_to_waypoints(json.load(f))

    if not waypoints:
        logger.warning("적재할 데이터 없음: %s", filepath)
        return

    conn = _get_connection(database_url)
    try:
        _ensure_table(conn)
        inserted, duplicated, skipped = _load_records(conn, waypoints)
        logger.info("%s: 적재 %d건, 중복 %d건, 실패 %d건", filepath, inserted, duplicated, skipped)
    finally:
        conn.close()


def _main() -> None:
    """CLI 진입점: JSON 파일을 읽어 PostGIS에 적재."""
    logging.basicConfig(level=logging.INFO)

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL 환경변수를 설정해주세요.")

    parser = argparse.ArgumentParser(description="waypoints PostGIS 적재")
    parser.add_argument(
        "--file",
        action="append",
        required=True,
        help="적재할 JSON 파일 경로 (여러 번 지정 가능)",
    )
    args = parser.parse_args()

    for filepath in args.file:
        try:
            load_from_file(filepath, database_url)
        except Exception as e:
            logger.error("파일 처리 실패 (%s): %s", filepath, e)


if __name__ == "__main__":
    _main()
