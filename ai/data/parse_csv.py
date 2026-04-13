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
from typing import Optional

from ai.models.waypoint import WaypointModel, WaypointType

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


def parse_bus_terminals(filepath: str) -> list[WaypointModel]:
    """버스 CSV에서 터미널만 추출해 WaypointModel 리스트 반환."""
    results = []
    skipped = 0

    with open(filepath, encoding=_ENCODING, errors="replace") as f:
        reader = csv.reader(f)
        try:
            next(reader)  # 헤더 스킵
        except StopIteration:
            return results

        for row in reader:
            if len(row) <= _BUS_COL_REGION:
                continue

            name = row[_BUS_COL_NAME].strip()
            if "터미널" not in name:
                continue

            lat = _parse_float(row[_BUS_COL_LAT])
            lng = _parse_float(row[_BUS_COL_LNG])

            if lat is None or lng is None:
                skipped += 1
                continue

            region = row[_BUS_COL_REGION].strip()

            try:
                results.append(WaypointModel(
                    name=name,
                    type=WaypointType.BUS,
                    latitude=lat,
                    longitude=lng,
                    address=region or None,
                    source="버스정류소CSV_터미널필터",
                ))
            except (ValueError, TypeError):
                skipped += 1

    if skipped:
        print(f"[버스] 좌표 오류로 제외: {skipped}건")

    return results


def parse_train_stations(filepath: str) -> list[WaypointModel]:
    """기차역 CSV에서 운행 중인 역만 추출해 WaypointModel 리스트 반환."""
    results = []
    skipped = 0

    with open(filepath, encoding=_ENCODING, errors="replace") as f:
        reader = csv.reader(f)
        try:
            next(reader)  # 헤더 스킵
        except StopIteration:
            return results

        for row in reader:
            if len(row) <= _TRAIN_COL_LNG:
                continue

            if row[_TRAIN_COL_CLOSED].strip() == "0":  # 폐역 제외
                continue

            name = row[_TRAIN_COL_NAME].strip()
            if not name:
                continue

            lat = _parse_float(row[_TRAIN_COL_LAT])
            lng = _parse_float(row[_TRAIN_COL_LNG])

            if lat is None or lng is None:
                skipped += 1
                continue

            address = row[_TRAIN_COL_ADDRESS].strip() or None

            try:
                results.append(WaypointModel(
                    name=name,
                    type=WaypointType.TRAIN,
                    latitude=lat,
                    longitude=lng,
                    address=address,
                    source="철도역CSV_운행중필터",
                ))
            except (ValueError, TypeError):
                skipped += 1

    if skipped:
        print(f"[기차] 좌표 오류로 제외: {skipped}건")

    return results


def _main():
    """CLI 진입점: 버스터미널·기차역 CSV 파싱 후 저장."""
    parser = argparse.ArgumentParser(description="버스터미널·기차역 CSV 파서")
    parser.add_argument("--bus", help="버스 CSV 파일 경로")
    parser.add_argument("--train", help="기차역 CSV 파일 경로")
    parser.add_argument("--output", help="저장할 JSON 파일 경로")
    args = parser.parse_args()

    output_data = {}

    if args.bus:
        buses = parse_bus_terminals(args.bus)
        print(f"버스터미널: {len(buses)}건")
        output_data["bus"] = [b.model_dump() for b in buses]

    if args.train:
        trains = parse_train_stations(args.train)
        print(f"기차역: {len(trains)}건")
        output_data["train"] = [t.model_dump() for t in trains]

    if args.output and output_data:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"저장 완료: {args.output}")


if __name__ == "__main__":
    _main()
