"""
waypoints PostGIS 적재 검증 스크립트

적재된 waypoints 데이터의 건수, 타입별 분포, 좌표 유효성을 확인한다.

실행:
    python -m ai.data.verify_waypoints
"""

import logging
import os

import psycopg2
import psycopg2.extras

logger = logging.getLogger(__name__)


def _get_connection(database_url: str) -> psycopg2.extensions.connection:
    """DATABASE_URL로 psycopg2 연결 반환."""
    return psycopg2.connect(database_url)


def verify(database_url: str) -> None:
    """waypoints 테이블 적재 결과 출력."""
    conn = _get_connection(database_url)
    try:
        _print_total(conn)
        _print_by_type(conn)
        _print_invalid_geom(conn)
    finally:
        conn.close()


def _print_total(conn: psycopg2.extensions.connection) -> None:
    """전체 건수 출력."""
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM waypoints")
        total = cur.fetchone()[0]
    logger.info("전체: %d건", total)


def _print_by_type(conn: psycopg2.extensions.connection) -> None:
    """타입별 건수 출력."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT type, COUNT(*) FROM waypoints GROUP BY type ORDER BY type"
        )
        rows = cur.fetchall()
    logger.info("타입별 분포:")
    for type_name, count in rows:
        logger.info("  %s: %d건", type_name, count)


def _print_invalid_geom(conn: psycopg2.extensions.connection) -> None:
    """좌표 범위 이상 항목 출력."""
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
    """CLI 진입점: waypoints 적재 결과 검증."""
    logging.basicConfig(level=logging.INFO)

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL 환경변수를 설정해주세요.")

    verify(database_url)


if __name__ == "__main__":
    _main()
