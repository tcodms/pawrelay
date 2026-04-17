import logging
import os

import psycopg2
import psycopg2.extras

logger = logging.getLogger(__name__)


def _get_connection(database_url: str) -> psycopg2.extensions.connection:
    return psycopg2.connect(database_url)


def verify(database_url: str) -> None:
    conn = _get_connection(database_url)
    try:
        _print_total(conn)
        _print_by_type(conn)
        _print_invalid_geom(conn)
    finally:
        conn.close()


def _print_total(conn: psycopg2.extensions.connection) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM waypoints")
        total = cur.fetchone()[0]
    logger.info("전체: %d건", total)


def _print_by_type(conn: psycopg2.extensions.connection) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT type, COUNT(*) FROM waypoints GROUP BY type ORDER BY type"
        )
        rows = cur.fetchall()
    logger.info("타입별 분포:")
    for type_name, count in rows:
        logger.info("  %s: %d건", type_name, count)


def _print_invalid_geom(conn: psycopg2.extensions.connection) -> None:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) FROM waypoints
            WHERE NOT ST_IsValid(geom)
               OR ST_X(geom) NOT BETWEEN 124 AND 132
               OR ST_Y(geom) NOT BETWEEN 33 AND 39
        """)
        invalid = cur.fetchone()[0]

    if invalid:
        logger.warning("좌표 이상 항목: %d건", invalid)
    else:
        logger.info("좌표 검증: 이상 없음")


def _main() -> None:
    logging.basicConfig(level=logging.INFO)

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL 환경변수를 설정해주세요.")

    verify(database_url)


if __name__ == "__main__":
    _main()
