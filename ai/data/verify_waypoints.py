"""
waypoints PostGIS 적재 검증 스크립트

적재된 waypoints 데이터의 건수, 타입별 분포, 좌표 유효성을 확인한다.

실행:
    python -m ai.data.verify_waypoints
"""

import os

import psycopg2
import psycopg2.extras


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
    print(f"전체: {total}건")


def _print_by_type(conn: psycopg2.extensions.connection) -> None:
    """타입별 건수 출력."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT type, COUNT(*) FROM waypoints GROUP BY type ORDER BY type"
        )
        rows = cur.fetchall()
    print("\n타입별 분포:")
    for type_name, count in rows:
        print(f"  {type_name}: {count}건")


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
        print(f"\n[경고] 좌표 이상 항목: {invalid}건")
    else:
        print("\n좌표 검증: 이상 없음")


def _main() -> None:
    """CLI 진입점: waypoints 적재 결과 검증."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL 환경변수를 설정해주세요.")

    verify(database_url)


if __name__ == "__main__":
    _main()
