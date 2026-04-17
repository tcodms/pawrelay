import argparse
import json
import logging
import os

import psycopg2
from pydantic import ValidationError

from ai.models.waypoint import WAYPOINT_TABLE_SQL, WAYPOINT_UNIQUE_INDEX_SQL, WaypointModel

logger = logging.getLogger(__name__)


class WaypointIndexError(Exception):
    pass


_INSERT_SQL = """
    INSERT INTO waypoints (name, type, address, phone, geom, source)
    VALUES (%(name)s, %(type)s, %(address)s, %(phone)s,
            ST_GeomFromEWKT(%(geom)s), %(source)s)
    ON CONFLICT (name, type) DO NOTHING
"""


def _get_connection(database_url: str) -> psycopg2.extensions.connection:
    return psycopg2.connect(database_url)


def _ensure_table(conn: psycopg2.extensions.connection) -> None:
    with conn.cursor() as cur:
        cur.execute(WAYPOINT_TABLE_SQL)
    conn.commit()
    _ensure_unique_index(conn)


def _ensure_unique_index(conn: psycopg2.extensions.connection) -> None:
    try:
        with conn.cursor() as cur:
            cur.execute(WAYPOINT_UNIQUE_INDEX_SQL)
        conn.commit()
    except psycopg2.Error as e:
        conn.rollback()
        logger.error("UNIQUE 인덱스 생성 실패: %s", e)
        raise WaypointIndexError(
            "waypoints(name, type) UNIQUE 인덱스를 생성하지 못해 적재를 중단합니다."
        ) from e


def _insert_one(cur, waypoint: WaypointModel) -> str:
    try:
        cur.execute("SAVEPOINT sp")
        cur.execute(_INSERT_SQL, waypoint.to_postgis_insert())
        result = "inserted" if cur.rowcount else "duplicated"
        cur.execute("RELEASE SAVEPOINT sp")
        return result
    except psycopg2.Error as e:
        logger.warning("적재 실패 (%s): %s", waypoint.name, e)
        cur.execute("ROLLBACK TO SAVEPOINT sp")
        try:
            cur.execute("RELEASE SAVEPOINT sp")
        except psycopg2.Error as release_err:
            logger.warning("SAVEPOINT 해제 실패: %s", release_err)
        return "skipped"


def _load_records(
    conn: psycopg2.extensions.connection,
    waypoints: list[WaypointModel],
) -> tuple[int, int, int]:
    counts: dict[str, int] = {"inserted": 0, "duplicated": 0, "skipped": 0}
    with conn.cursor() as cur:
        for waypoint in waypoints:
            counts[_insert_one(cur, waypoint)] += 1
    conn.commit()
    return counts["inserted"], counts["duplicated"], counts["skipped"]


def _parse_json_to_waypoints(data: dict) -> list[WaypointModel]:
    if not isinstance(data, dict):
        logger.warning("JSON 최상위 타입이 dict가 아님: %s", type(data).__name__)
        return []
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


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="waypoints PostGIS 적재")
    parser.add_argument(
        "--file",
        action="append",
        required=True,
        help="적재할 JSON 파일 경로 (여러 번 지정 가능)",
    )
    return parser


def _load_all_files(files: list[str], database_url: str) -> int:
    failed = 0
    for filepath in files:
        try:
            load_from_file(filepath, database_url)
        except WaypointIndexError as e:
            logger.error("파일 처리 실패 (%s): %s", filepath, e)
            raise SystemExit(1) from e
        except (OSError, json.JSONDecodeError, psycopg2.Error) as e:
            failed += 1
            logger.error("파일 처리 실패 (%s): %s", filepath, e)
    return failed


def _main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = _build_parser()
    args = parser.parse_args()
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        parser.error("DATABASE_URL 환경변수를 설정해주세요.")
    if _load_all_files(args.file, database_url):
        raise SystemExit(1)


if __name__ == "__main__":
    _main()
