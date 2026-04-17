"""
버스터미널·기차역 CSV 파일 파서

버스: TOTAL_sp_bus_stop_locations.csv
    - 인코딩: CP949
    - 컬럼: 정류소번호(0), 정류소명(1), 위도(2), 경도(3), ..., 지역명(7)
    - 필터: 정류소명에 "터미널" 포함

기차: 국가철도공단_철도역 정보_20250711.csv
    - 인코딩: CP949
    - 컬럼: 주소(0), 위도좌표(1), 운행여부(2), ..., 역이름(5), ..., 경도좌표(8)
    - 필터: 운행여부 != "0" (0=폐역 제외, 1/2/3=운행 중)

실행:
    python -m ai.data.parse_csv --bus path/to/bus.csv --train path/to/train.csv
    python -m ai.data.parse_csv --bus path/to/bus.csv
    python -m ai.data.parse_csv --train path/to/train.csv
"""

import argparse
import csv
import json
import logging
from typing import Optional

from ai.models.waypoint import WaypointModel, WaypointType

logger = logging.getLogger(__name__)

_ENCODING = "cp949"

# 버스 CSV 컬럼 인덱스
_BUS_COL_NAME = 1
_BUS_COL_LAT = 2
_BUS_COL_LNG = 3
_BUS_COL_REGION = 7

# 기차 CSV 컬럼 인덱스
_TRAIN_COL_ADDRESS = 0
_TRAIN_COL_LAT = 1
_TRAIN_COL_CLOSED = 2   # 0 = 폐역, 1/2/3 = 운행 중
_TRAIN_COL_NAME = 5
_TRAIN_COL_LNG = 8


def _parse_float(value: str) -> Optional[float]:
    """문자열을 float으로 변환. 실패 시 None 반환."""
    try:
        return float(value.strip())
    except (ValueError, AttributeError):
        return None


def _build_bus_waypoint(row: list[str]) -> Optional[WaypointModel]:
    """버스 CSV 한 행을 WaypointModel로 변환. 유효하지 않으면 None 반환."""
    if len(row) <= _BUS_COL_REGION:
        return None
    name = row[_BUS_COL_NAME].strip()
    if "터미널" not in name:
        return None
    lat = _parse_float(row[_BUS_COL_LAT])
    lng = _parse_float(row[_BUS_COL_LNG])
    if lat is None or lng is None:
        return None
    region = row[_BUS_COL_REGION].strip() or None
    return WaypointModel(
        name=name,
        type=WaypointType.BUS,
        latitude=lat,
        longitude=lng,
        address=region,
        source="버스정류소CSV_터미널필터",
    )


def _validate_train_row(row: list[str]) -> bool:
    """기차 CSV 행 유효성 검사. 유효하면 True."""
    if len(row) <= _TRAIN_COL_LNG:
        return False
    if row[_TRAIN_COL_CLOSED].strip() == "0":
        return False
    return bool(row[_TRAIN_COL_NAME].strip())


def _build_train_waypoint(row: list[str]) -> Optional[WaypointModel]:
    """기차 CSV 한 행을 WaypointModel로 변환. 유효하지 않으면 None 반환."""
    if not _validate_train_row(row):
        return None
    name = row[_TRAIN_COL_NAME].strip()
    lat = _parse_float(row[_TRAIN_COL_LAT])
    lng = _parse_float(row[_TRAIN_COL_LNG])
    if lat is None or lng is None:
        return None
    return WaypointModel(
        name=name,
        type=WaypointType.TRAIN,
        latitude=lat,
        longitude=lng,
        address=row[_TRAIN_COL_ADDRESS].strip() or None,
        source="철도역CSV_운행중필터",
    )


def _iter_csv_rows(filepath: str) -> csv.reader:
    """CP949 CSV 파일을 열고 헤더를 스킵한 reader 반환."""
    f = open(filepath, encoding=_ENCODING, errors="replace")
    reader = csv.reader(f)
    try:
        next(reader)
    except StopIteration:
        pass
    return reader


def parse_bus_terminals(filepath: str) -> list[WaypointModel]:
    """버스 CSV에서 터미널만 추출해 WaypointModel 리스트 반환."""
    results = []
    skipped = 0
    for row in _iter_csv_rows(filepath):
        try:
            waypoint = _build_bus_waypoint(row)
            if waypoint:
                results.append(waypoint)
        except (ValueError, TypeError):
            skipped += 1
    if skipped:
        logger.warning("[버스] 오류로 제외: %d건", skipped)
    return results


def parse_train_stations(filepath: str) -> list[WaypointModel]:
    """기차역 CSV에서 운행 중인 역만 추출해 WaypointModel 리스트 반환."""
    results = []
    skipped = 0
    for row in _iter_csv_rows(filepath):
        try:
            waypoint = _build_train_waypoint(row)
            if waypoint:
                results.append(waypoint)
        except (ValueError, TypeError):
            skipped += 1
    if skipped:
        logger.warning("[기차] 오류로 제외: %d건", skipped)
    return results


def _build_parser() -> argparse.ArgumentParser:
    """CLI 인자 파서 생성."""
    parser = argparse.ArgumentParser(description="버스터미널·기차역 CSV 파서")
    parser.add_argument("--bus", help="버스 CSV 파일 경로")
    parser.add_argument("--train", help="기차역 CSV 파일 경로")
    parser.add_argument("--output", help="저장할 JSON 파일 경로")
    return parser


def _collect_data(args) -> dict:
    """인자에 따라 버스/기차 데이터 수집 후 dict 반환."""
    output_data = {}
    if args.bus:
        buses = parse_bus_terminals(args.bus)
        logger.info("버스터미널: %d건", len(buses))
        output_data["bus"] = [b.model_dump() for b in buses]
    if args.train:
        trains = parse_train_stations(args.train)
        logger.info("기차역: %d건", len(trains))
        output_data["train"] = [t.model_dump() for t in trains]
    return output_data


def _main():
    """CLI 진입점: 버스터미널·기차역 CSV 파싱 후 저장."""
    logging.basicConfig(level=logging.INFO)
    parser = _build_parser()
    args = parser.parse_args()
    if not args.bus and not args.train:
        parser.error("--bus 또는 --train 중 하나 이상 지정해주세요.")
    output_data = _collect_data(args)
    if args.output and output_data:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        logger.info("저장 완료: %s", args.output)


if __name__ == "__main__":
    _main()
